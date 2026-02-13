#include <iostream>
#include <ctime>
#include <omp.h>
#include <fstream>
#include <string>
#include <immintrin.h>

using namespace std;

// Funkcija za GCD (Euclidean algorithm)
long long gcd(long long a, long long b) {

    while (b != 0) {
        long long t = b;
        b = a % b;
        a = t;
    }

    return a;
}


inline long long modMult_branchless(long long a, long long b, long long mod) {
    
    long long result = 0;
    a %= mod;

    while (b > 0) {

        result += a * (b & 1);

        if (result >= mod) 
            result -= mod;

        a <<= 1;

        if (a >= mod)
            a -= mod;

        b >>= 1;
    }
    return result;
}

// Modularna eksponencija (bit-po-bit)
long long modularExponentiation(long long base, long long exp, long long modul) {

    long long res = 1;
    base %= modul;

    while (exp > 0) {
        if (exp & 1) 
            res = modMult_branchless(res, base, modul);

        base = modMult_branchless(base, base, modul);
        exp >>= 1;
    }

    return res;
}

// Extended Euclidean algorithm za modularni inverz
long long modInverse(long long a, long long m) {

    long long m0 = m, t, q;
    long long x0 = 0, x1 = 1;

    while (a > 1) {
        q = a / m;
        t = m;
        m = a % m;
        a = t;
        t = x0;
        x0 = x1 - q * x0;
        x1 = t;
    }

    if (x1 < 0) 
        x1 += m0;

    return x1;
}

// RSA dekripcija sa CRT 
inline long long decryptCRT(long long c, long long dp, long long dq, long long p, long long q, long long qInv) {

    long long m1 = modularExponentiation(c % p, dp, p);
    long long m2 = modularExponentiation(c % q, dq, q);

    long long diff = m1 - m2;
    diff += (diff >> 63) & p;

    long long h = modMult_branchless(qInv, diff, p);

    return m2 + h * q;
}



bool verifyRSA(const long long* original, const long long* decrypted, long long size) {

    const long long* end = original + size;

    while (original != end) {
        if (*original != *decrypted)
            return false;
        original++;
        decrypted++;
    }
    return true;
}


bool verifyRSA_par(const long long* original, const long long* decrypted, long long size)
{
    long long i = 0;

    for (; i + 4 <= size; i += 4) {

        __m256i a = _mm256_loadu_si256((__m256i const*)(original + i));
        __m256i b = _mm256_loadu_si256((__m256i const*)(decrypted + i));

        __m256i cmp = _mm256_cmpeq_epi64(a, b);

        int mask = _mm256_movemask_pd(_mm256_castsi256_pd(cmp));

        if (mask != 0xF)    
            return false;
    }

     for (; i < size; i++)
        if (original[i] != decrypted[i])
            return false;

    return true;
}



double test_serial_txt(const std::string& filename) {

    // --- Učitavanje iz fajla ---
    std::ifstream f_orig(filename);
    if (!f_orig.is_open()) {
        std::cerr << "Ne moze se otvoriti " << filename << std::endl;
        exit(1);
    }

    std::string content((std::istreambuf_iterator<char>(f_orig)),
        std::istreambuf_iterator<char>());
    f_orig.close();

    long long num_messages = content.size();

    long long* Message = new long long[num_messages];
    long long* encrypted = new long long[num_messages];
    long long* decrypted = new long long[num_messages];

    for (long long i = 0; i < num_messages; i++)
        Message[i] = (long long)content[i];

    // Generiranje ključeva
    long long p = 6043, q = 4813, n = p * q, phi = (p - 1) * (q - 1);
    long long e = 65537;
    while (gcd(e, phi) != 1) e++;
    long long d = modInverse(e, phi);
    long long dp = d % (p - 1), dq = d % (q - 1), qInv = modInverse(q, p);
    
    double start = omp_get_wtime();

    // Serijska enkripcija
    for (long long i = 0; i < num_messages; i++)
        encrypted[i] = modularExponentiation(Message[i], e, n);

    // Serijska dekripcija
    for (long long i = 0; i < num_messages; i++)
        decrypted[i] = decryptCRT(encrypted[i], dp, dq, p, q, qInv);

    bool test = verifyRSA(Message, decrypted, num_messages);

    double end = omp_get_wtime();

    if (!test) 
        cout << "GRESKA u serijskoj enkripciji/dekripciji!" << endl;

    std::ofstream f_enc("enc.txt");

    for (long long i = 0; i < num_messages; i++)
        f_enc << encrypted[i] << " ";
    f_enc.close();

    std::ofstream f_dec("dec.txt");

    for (long long i = 0; i < num_messages; i++)
        f_dec << static_cast<char>(decrypted[i]);
    f_dec.close();

    delete[] Message;
    delete[] encrypted;
    delete[] decrypted;

    return end - start;
}


double test_parallel_txt(const std::string& filename) {

    // --- Učitavanje iz fajla ---
    std::ifstream f_orig(filename);
    if (!f_orig.is_open()) {
        std::cerr << "Ne moze se otvoriti " << filename << std::endl;
        exit(1);
    }

    std::string content((std::istreambuf_iterator<char>(f_orig)),
        std::istreambuf_iterator<char>());
    f_orig.close();

    long long num_messages = content.size();

    long long* Message = new long long[num_messages];
    long long* encrypted = new long long[num_messages];
    long long* decrypted = new long long[num_messages];

    for (long long i = 0; i < num_messages; i++)
        Message[i] = (long long)content[i];

    // Generiranje ključeva
    long long p = 6043, q = 4813, n = p * q, phi = (p - 1) * (q - 1);
    long long e = 65537;
    while (gcd(e, phi) != 1) e++;
    long long d = modInverse(e, phi);
    long long dp = d % (p - 1), dq = d % (q - 1), qInv = modInverse(q, p);

    double start = omp_get_wtime();


    // Paralelna enkripcija
#pragma omp parallel for
    for (long long i = 0; i < num_messages; i++)
        encrypted[i] = modularExponentiation(Message[i], e, n);

    // Paralelna dekripcija
#pragma omp parallel for
    for (long long i = 0; i < num_messages; i++)
        decrypted[i] = decryptCRT(encrypted[i], dp, dq, p, q, qInv);

    bool test = verifyRSA_par(Message, decrypted, num_messages);

    double end = omp_get_wtime();


    if (!test)
        cout << "GRESKA u paralelnoj enkripciji/dekripciji!" << endl;

    delete[] Message;
    delete[] encrypted;
    delete[] decrypted;

    return end - start;
}

int main(int argc, char* argv[])
{
    bool checked = false;
    int maxT = omp_get_max_threads();
    omp_set_num_threads(maxT);

    if (argc >= 2 && std::string(argv[1]) == "checked") {
        checked = true;
    }

    cout << "\nPokretanje testova..." << endl;

    double serial_times;
    double parallel_times;

    double total_serial_time = 0.0;
    double total_parallel_time = 0.0;

    // --- PUTANJA DO TEKSTA ---
    std::string txt_file = "original.txt";

    // Testiranje serijske verzije
    double run_time = test_serial_txt(txt_file);
    total_serial_time += run_time;
    serial_times = run_time;
    cout << "Serijski ciklus: " << run_time << " s" << endl;
    cout << "------------------------------------------" << endl;

    for (int i = 1; i <= maxT; i++) {

        if (checked) {
            omp_set_num_threads(i);
            cout << endl << "Maksimalan broj threadova (OpenMP): " << i << endl;
            cout << "------------------------------------------" << endl;
        }
        else {
            i = omp_get_max_threads();
            omp_set_num_threads(i);
            cout << endl << "Maksimalan broj threadova (OpenMP): " << omp_get_max_threads() << endl;
            cout << "------------------------------------------" << endl;
        }

        // Testiranje paralelne verzije
        run_time = test_parallel_txt(txt_file);
        total_parallel_time += run_time;
        parallel_times = run_time;
        cout << "Paralelni ciklus: " << run_time << " s" << endl;
        cout << "------------------------------------------" << endl;

        // Finalni rezultati
        cout << "---- FINALNI REZULTATI ----" << endl;
        cout << "Serijsko vrijeme: " << serial_times << " s" << endl;
        cout << "Paralelno vrijeme: " << parallel_times << " s" << endl;

        cout << "Ubrzanje (Speedup): " << serial_times / parallel_times << "x" << endl;

        // ------------------ ZAPIS U CSV ------------------
        std::string csv_name = "rsa_output.csv";

        ofstream file(csv_name, ios::app);

        if (file.is_open()) {

            file << serial_times << "," << parallel_times << "," << i << "\n";
            file.close();
        }
        else {
            cerr << "Greska: Ne moze se otvoriti CSV file!\n";
        }

        cout << "------------------------------------------" << endl;

    }

    return 0;
}