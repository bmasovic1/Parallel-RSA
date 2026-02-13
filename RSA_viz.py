import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk
import subprocess
import os
import random
import matplotlib.pyplot as plt
import csv

from pathlib import Path

# ---------------------- PUTANJE ----------------------

BASE_DIR = Path(__file__).resolve().parent

ORIGINAL_FILE = BASE_DIR / "original.txt"
ENC_FILE      = BASE_DIR / "enc.txt"
DEC_FILE      = BASE_DIR / "dec.txt"
CSV_FILE      = BASE_DIR / "rsa_output.csv"
PNG_FILE      = BASE_DIR / "rsa_performance.png"
EXE_PATH      = BASE_DIR / "RSA.exe"



MAX_SHOW = 500  # koliko rijeci prikazati u panelu

# ---------------------- FUNKCIJE ----------------------
def latin_simplify(text):
    replacements = {
        "č": "c", "ć": "c", "š": "s", "ž": "z", "đ": "d",
        "Č": "C", "Ć": "C", "Š": "S", "Ž": "Z", "Đ": "D",
        "dž": "dz", "Dž": "Dz", "DŽ": "DZ",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def read_file_limited(filepath, max_words=MAX_SHOW):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().split()
        limited_content = content[:max_words]
        return " ".join(limited_content) + (" ... (prikaz skracen)" if len(content) > max_words else "")
    except Exception as e:
        return f"Greska pri citanju {filepath}:\n{e}"

def generate_massive_text():
    open(ENC_FILE, "w").close()
    open(DEC_FILE, "w").close()

    enc_text.delete(1.0, tk.END)
    dec_text.delete(1.0, tk.END)

    try:
        total_words = int(words_entry.get())
        if total_words <= 0:
            raise ValueError
    except:
        messagebox.showerror("Greska", "Unesite ispravan broj rijeci (pozitivan cijeli broj)")
        return

    titles = [
        "Uvod u RSA", "Matematicka Osnova RSA", "Generisanje Kljuceva",
        "Enkripcija i Dekripcija", "Modularna Eksponencija", "Extended Euclidean Algorithm",
        "CRT (Kineski Teorem o Ostatcima)", "Sigurnosni Aspekti", "Napadi i Zastita",
        "Paralelizacija RSA", "GPU Implementacija", "CPU Multi-threading",
        "Batch Enkripcija", "Analiza Performansi", "Prakticne Primjene",
        "Hibridni Kripto Sistemi", "Buduci Pravci", "Post-kvantna Kriptografija", "Zakljucak"
    ]

    base_sentences = [
        "Ova sekcija detaljno objasnjava sve aspekte {title}.",
        "Primjer implementacije, matematicki dokaz, i paralelizacija su ukljuceni.",
        "Objasnjenje koraka, sigurnosnih rizika i optimizacija u praksi.",
        "Detaljna analiza modularne eksponencije i CRT dekripcije.",
        "Diskusija o performansama CPU i GPU implementacija.",
        "Sigurnosni napadi i zastita od vremenskih i side-channel napada.",
        "Uloga hibridnih kripto sistema i post-kvantna kriptografija.",
        "Primjena paralelizacije u batch enkripciji i dekripciji.",
        "Detaljna teorija i primjeri koda u C++ i Pythonu."
    ]

    def gen_sentence(title):
        return random.choice(base_sentences).format(title=title)

    words_generated = 0
    chunks = []

    while words_generated < total_words:
        for title in titles:
            remaining = total_words - words_generated
            if remaining <= 0:
                break
            num_words = min(random.randint(50, 150), remaining)
            sentences = [gen_sentence(title) for _ in range(num_words)]
            chunks.append(" ".join(sentences))
            words_generated += num_words

    full_text = "\n\n".join(chunks)
    full_text = latin_simplify(full_text)

    try:
        with open(ORIGINAL_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)

        original_text.delete(1.0, tk.END)
        original_text.insert(tk.END, read_file_limited(ORIGINAL_FILE))

    except Exception as e:
        messagebox.showerror("Greska", f"Ne mogu spremiti original.txt:\n{e}")

def run_rsa():
    try:
        if use_all_threads_var.get() == 1:
            subprocess.run([EXE_PATH, "checked"], check=True)
        else:
            subprocess.run([EXE_PATH], check=True)

        original_text.delete(1.0, tk.END)
        enc_text.delete(1.0, tk.END)
        dec_text.delete(1.0, tk.END)

        original_text.insert(tk.END, read_file_limited(ORIGINAL_FILE))

        try:
            with open(ENC_FILE, "r", encoding="utf-8") as f:
                enc_numbers = f.read().split()
            limited_enc = enc_numbers[:MAX_SHOW]
            lines = [" ".join(limited_enc[i:i + 10]) for i in range(0, len(limited_enc), 10)]
            enc_text.insert(tk.END, "\n".join(lines) + ("\n... (prikaz skracen)" if len(enc_numbers) > MAX_SHOW else ""))
        except Exception as e:
            enc_text.insert(tk.END, f"Greska pri citanju {ENC_FILE}:\n{e}")

        dec_text.insert(tk.END, read_file_limited(DEC_FILE))

    except Exception as e:
        messagebox.showerror("Greska", f"Doslo je do greske:\n{e}")

def populate_thread_choices():
    threads_set = set()
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        t = int(row['threads'])
                        threads_set.add(t)
                    except:
                        pass
        except:
            threads_set = set()

    if not threads_set:
        defaults = [1, 2, 4, 6, 8, 12, 16, 24, 32]
        return [str(x) for x in defaults]

    sorted_threads = sorted(list(threads_set))
    return [str(x) for x in sorted_threads]

def get_selected_thread_int():
    val = thread_combobox.get()
    try:
        return int(val)
    except:
        return None

def show_graph():
    try:
        if not os.path.exists(CSV_FILE):
            messagebox.showwarning("Upozorenje", f"CSV file nije pronadjen: {CSV_FILE}")
            return

        selected_t = get_selected_thread_int()
        if selected_t is None:
            messagebox.showwarning("Upozorenje", "Odaberite broj threadova iz liste")
            return

        serial, parallel = [], []
        with open(CSV_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    if int(row['threads']) == selected_t:
                        serial.append(float(row['serial']))
                        parallel.append(float(row['parallel']))
                except:
                    pass

        if not serial or not parallel:
            messagebox.showwarning("Upozorenje", f"Nema podataka za threads = {selected_t}")
            return

        runs = list(range(1, len(serial) + 1))
        avg_serial = sum(serial) / len(serial)
        avg_parallel = sum(parallel) / len(parallel)
        speedup = avg_serial / avg_parallel if avg_parallel != 0 else float('inf')

        plt.figure(figsize=(10, 6))
        plt.plot(runs, serial, marker='o', label='Serial', color='blue')
        plt.plot(runs, parallel, marker='o', label='Parallel', color='orange')

        ymax_val = max(max(serial), max(parallel))
        for x, y in zip(runs, serial):
            plt.text(x, y + 0.01 * ymax_val, f"{y:.2f}", ha='center', va='bottom', fontsize=9, color='blue')
        for x, y in zip(runs, parallel):
            plt.text(x, y + 0.01 * ymax_val, f"{y:.2f}", ha='center', va='bottom', fontsize=9, color='orange')

        plt.axhline(y=avg_serial, color='blue', linestyle='--', label='Avg Serial')
        plt.axhline(y=avg_parallel, color='orange', linestyle='--', label='Avg Parallel')

        y_min = 0
        y_max = ymax_val * 1.2
        plt.ylim(y_min, y_max)

        plt.text(0.5 * (runs[0] + runs[-1]), y_max * 0.95,
                 f"Speedup: {speedup:.2f}x", fontsize=12, fontweight='bold',
                 ha='center', va='top', color='green')

        plt.xlabel("Run")
        plt.ylabel("Vrijeme (s)")
        plt.title(f"RSA Performanse: Serijska vs Paralelna (threads = {selected_t})")
        plt.xticks(runs)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(PNG_FILE, dpi=300)
        plt.show()

    except Exception as e:
        messagebox.showerror("Greska", f"Doslo je do greske pri prikazu grafa:\n{e}")

def show_speedup_by_threads():
    try:
        if not os.path.exists(CSV_FILE):
            messagebox.showwarning("Upozorenje", f"CSV file nije pronadjen: {CSV_FILE}")
            return

        rows = []

        with open(CSV_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    t = int(row['threads'])
                    s = float(row['serial'])
                    p = float(row['parallel'])
                    rows.append((t, s, p))
                except:
                    pass

        if not rows:
            messagebox.showwarning("Upozorenje", "CSV je prazan ili nevalidan")
            return

        series_list = []
        i = 0

        while i < len(rows):
            if rows[i][0] == 1:
                temp = [rows[i]]
                j = i + 1
                expected = 2

                while j < len(rows):
                    t, s, p = rows[j]
                    if t == expected:
                        temp.append(rows[j])
                        expected += 1
                    else:
                        break
                    j += 1

                if len(temp) >= 2:
                    series_list.append(temp)

                i = j
            else:
                i += 1

        if not series_list:
            messagebox.showwarning("Upozorenje", "CSV ne sadrzi nijednu kompletnu seriju 1..N")
            return

        final_series = series_list[-1]

        threads = [row[0] for row in final_series]
        parallel = [row[2] for row in final_series]

        plt.figure(figsize=(12, 6))
        plt.plot(threads, parallel, marker='o', linestyle='-', label='Paralelno')

        ymax = max(parallel)
        offset = ymax * 0.02

        for x, y in zip(threads, parallel):
            plt.text(x, y + offset, f"{y:.2f}", ha='center', fontsize=9)

        plt.title("Performanse RSA u odnosu na broj threadova")
        plt.xlabel("Broj threadova")
        plt.ylabel("Vrijeme (s)")
        plt.xticks(threads)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.show()

    except Exception as e:
        messagebox.showerror("Greska", f"Greska pri prikazu speedup grafa:\n{e}")

# ---------------------- GUI ----------------------
root = tk.Tk()
root.title("RSA Vizualizacija")
root.geometry("1200x650")

def create_panel(title, row, column):
    frame = tk.Frame(root, bd=1, relief=tk.SUNKEN)
    frame.grid(row=row, column=column, sticky="nsew", padx=2, pady=2)
    tk.Label(frame, text=title, font=("Arial", 12, "bold")).pack(side=tk.TOP, fill=tk.X)
    txt = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
    txt.pack(fill=tk.BOTH, expand=True)
    return txt

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_rowconfigure(1, weight=1)

original_text = create_panel("Original", 1, 0)
enc_text = create_panel("Encrypted", 1, 1)
dec_text = create_panel("Decrypted", 1, 2)

original_controls = tk.Frame(root)
original_controls.grid(row=0, column=0, sticky="n")
words_entry = tk.Entry(original_controls, width=15)
words_entry.pack(side=tk.LEFT, padx=5)
words_entry.insert(0, "1000000")
tk.Button(original_controls, text="Generisanje teksta", command=generate_massive_text).pack(side=tk.LEFT, padx=5)

enc_controls = tk.Frame(root)
enc_controls.grid(row=0, column=1, sticky="n")

use_all_threads_var = tk.IntVar(value=0)
tk.Label(enc_controls, text="RSA kroz sve threadove:").pack(side=tk.LEFT, padx=5)
tk.Checkbutton(enc_controls, variable=use_all_threads_var).pack(side=tk.LEFT, padx=5)
tk.Button(enc_controls, text="Pokreni RSA", command=run_rsa).pack(side=tk.LEFT, padx=5)

# ---------------------- Combobox premjesten u dec_controls ----------------------
dec_controls = tk.Frame(root)
dec_controls.grid(row=0, column=2, sticky="n")

thread_values = populate_thread_choices()
tk.Label(dec_controls, text="Broj threadova:").pack(side=tk.LEFT, padx=(12,2))
thread_combobox = ttk.Combobox(dec_controls, values=thread_values, state="readonly", width=6)
if thread_values:
    thread_combobox.set(thread_values[0])
thread_combobox.pack(side=tk.LEFT, padx=2)

tk.Button(dec_controls, text="Prikazi Graf", command=show_graph).pack(side=tk.LEFT, padx=5)
tk.Button(dec_controls, text="Ubrzanje po threadovima", command=show_speedup_by_threads).pack(side=tk.LEFT, padx=5)

# ---------------------- CLEAR ON START ----------------------
def clear_text_files():
    for path in [ORIGINAL_FILE, ENC_FILE, DEC_FILE]:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            print(f"Ne mogu obrisati {path}: {e}")

clear_text_files()

root.mainloop()
