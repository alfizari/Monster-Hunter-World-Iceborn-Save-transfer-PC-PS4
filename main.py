import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import mhw as PC
import ps4 as PS4
import threading


PC_REGIONS={
    1: {'start': 0x3010D8, 'end': 0x3010D8 + 0x2098C0},
    2: {'start': 0x50AB98, 'end': 0x50AB98 + 0x2098C0},
    3: {'start': 0x714658, 'end': 0x714658 + 0x2098C0},
}

PS4_REGIONS={
    1: {'start': 0x488, 'end': 0x488 + 0x2098C0},
    2: {'start': 0x209F48, 'end': 0x209F48 + 0x2098C0},
    3: {'start': 0x413A08, 'end': 0x413A08 + 0x2098C0},
}

SLOT_SIZE = 0x61D040  # size of one save slot


def read_file(file_path):
    with open(file_path, 'rb') as f:
        data = bytearray(f.read())
    if not data:
        print('No data found')
        return
    return data


def write_file(data, out_put_path):
    if not data:
        print('No data found to write')
        return
    if not out_put_path:
        print('No output path given')
        return
    with open(out_put_path, 'wb') as f:
        f.write(data)


def ps4_to_pc(ps4_slot, pc_slot):
    try:
        pc_file_path = filedialog.askopenfilename(title='Select your PC save')
        file_name = os.path.basename(pc_file_path)
        pc_data = read_file(pc_file_path)
        pc_data_decrypted = PC.decrypt_save(pc_data)

        ps4_file_path = filedialog.askopenfilename(title='Select your PS4 save', defaultextension='.dat')
        ps4_data = read_file(ps4_file_path)

        if (
            ps4_data[0x48A] == 0 or
            ps4_data[0x48B] == 0 or
            ps4_data[0x4A4] == 0 or
            ps4_data[0x7B9] == 0
        ):
            ps4_data_decrypted = ps4_data[:0x600488] + ps4_data[0x6010C0:]
        else:
            ps4_data = ps4_data[:0x600488] + ps4_data[0x6010C0:]
            ps4_data_decrypted = PS4.decrypt_save(ps4_data)

        # Read source slot from PS4
        ps4_start = PS4_REGIONS[ps4_slot]['start']
        ps4_slot_data = ps4_data_decrypted[ps4_start: ps4_start + SLOT_SIZE]

        # Write into destination slot on PC
        pc_start = PC_REGIONS[pc_slot]['start']
        pc_data_decrypted = bytearray(
            pc_data_decrypted[:pc_start] +
            ps4_slot_data +
            pc_data_decrypted[pc_start + SLOT_SIZE:]
        )

        pc_data_encrypted = PC.encrypt_save(bytearray(pc_data_decrypted))

        out_path = filedialog.asksaveasfilename(
            title='Select where to save your PC save',
            initialfile=file_name
        )
        write_file(pc_data_encrypted, out_path)
        print('Save transferred')

    except Exception as e:
        messagebox.showerror("Error", str(e))


def pc_to_ps4(pc_slot, ps4_slot):
    try:
        DECRYPTED = False

        ps4_path = filedialog.askopenfilename(title='Select your PS4 save')
        ps4_data = read_file(ps4_path)
        add_back = ps4_data[0x600488:0x6010C0]

        if (
            ps4_data[0x48A] == 0 or
            ps4_data[0x48B] == 0 or
            ps4_data[0x4A4] == 0 or
            ps4_data[0x7B9] == 0
        ):
            ps4_data_without_extra = ps4_data[:0x600488] + ps4_data[0x6010C0:]
            ps4_data_decrypted = ps4_data_without_extra
            DECRYPTED = True
        else:
            ps4_data_without_extra = ps4_data[:0x600488] + ps4_data[0x6010C0:]
            ps4_data_decrypted = PS4.decrypt_save(ps4_data_without_extra)

        pc_file_path = filedialog.askopenfilename(title='Select your PC save')
        pc_data = read_file(pc_file_path)
        pc_data_decrypted = PC.decrypt_save(pc_data)

        # Read source slot from PC
        pc_start = PC_REGIONS[pc_slot]['start']
        pc_slot_data = pc_data_decrypted[pc_start: pc_start + SLOT_SIZE]

        # Write into destination slot on PS4
        ps4_start = PS4_REGIONS[ps4_slot]['start']
        ps4_data_decrypted = bytearray(
            ps4_data_decrypted[:ps4_start] +
            pc_slot_data +
            ps4_data_decrypted[ps4_start + SLOT_SIZE:]
        )

        if not DECRYPTED:
            ps4_data_encrypted_without_extra = bytearray(PS4.encrypt_save(ps4_data_decrypted))
            ps4_data_encrypted = ps4_data_encrypted_without_extra[:0x600488] + add_back + ps4_data_encrypted_without_extra[0x600488:]
        else:
            ps4_data_encrypted = ps4_data_decrypted[:0x600488] + add_back + ps4_data_decrypted[0x600488:]

        out_path = filedialog.asksaveasfilename(
            title='Select where to save your file',
            initialfile='memory.dat',
            defaultextension='.dat',
            filetypes=[('DAT files', '*.dat'), ('All files', '*.*')]
        )
        write_file(ps4_data_encrypted, out_path)
        print('Save transferred')

    except Exception as e:
        messagebox.showerror("Error", str(e))


def run_with_progress(task_function):
    def task():
        try:
            task_function()
            messagebox.showinfo("Success", "Operation completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            progress.stop()

    progress.start(10)
    threading.Thread(target=task, daemon=True).start()


# ── GUI ──────────────────────────────────────────────────────────────────────

root = tk.Tk()
root.title("MHW Save Converter")
root.geometry("500x340")
root.resizable(False, False)

progress = ttk.Progressbar(root, mode="indeterminate")
progress.pack(side="bottom", fill="x", padx=10, pady=5)

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

SLOT_OPTIONS = ["Slot 1", "Slot 2", "Slot 3"]

# ── Tab 1: PS4 ➜ PC ──────────────────────────────────────────────────────────
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text="PS4 ➜ PC")

tk.Label(tab1, text="Instructions:\n\n"
         "1. Choose source PS4 slot and destination PC slot\n"
         "2. Select your PC save (base file)\n"
         "3. Select your PS4 save\n"
         "4. Choose where to save the new PC file",
         justify="left").pack(pady=10)

slot_frame1 = ttk.Frame(tab1)
slot_frame1.pack(pady=5)

tk.Label(slot_frame1, text="PS4 source slot:").grid(row=0, column=0, padx=8)
ps4_src_var = tk.StringVar(value="Slot 1")
ttk.Combobox(slot_frame1, textvariable=ps4_src_var, values=SLOT_OPTIONS,
             state="readonly", width=10).grid(row=0, column=1, padx=8)

tk.Label(slot_frame1, text="PC destination slot:").grid(row=0, column=2, padx=8)
pc_dst_var = tk.StringVar(value="Slot 1")
ttk.Combobox(slot_frame1, textvariable=pc_dst_var, values=SLOT_OPTIONS,
             state="readonly", width=10).grid(row=0, column=3, padx=8)

tk.Button(
    tab1, text="Convert PS4 ➜ PC",
    command=lambda: run_with_progress(
        lambda: ps4_to_pc(
            int(ps4_src_var.get().split()[1]),
            int(pc_dst_var.get().split()[1])
        )
    ),
    width=25, height=2
).pack(pady=10)

# ── Tab 2: PC ➜ PS4 ──────────────────────────────────────────────────────────
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="PC ➜ PS4")

tk.Label(tab2, text="Instructions:\n\n"
         "1. Choose source PC slot and destination PS4 slot\n"
         "2. Select your PS4 save (base file)\n"
         "3. Select your PC save\n"
         "4. Choose where to save the new PS4 file",
         justify="left").pack(pady=10)

slot_frame2 = ttk.Frame(tab2)
slot_frame2.pack(pady=5)

tk.Label(slot_frame2, text="PC source slot:").grid(row=0, column=0, padx=8)
pc_src_var = tk.StringVar(value="Slot 1")
ttk.Combobox(slot_frame2, textvariable=pc_src_var, values=SLOT_OPTIONS,
             state="readonly", width=10).grid(row=0, column=1, padx=8)

tk.Label(slot_frame2, text="PS4 destination slot:").grid(row=0, column=2, padx=8)
ps4_dst_var = tk.StringVar(value="Slot 1")
ttk.Combobox(slot_frame2, textvariable=ps4_dst_var, values=SLOT_OPTIONS,
             state="readonly", width=10).grid(row=0, column=3, padx=8)

tk.Button(
    tab2, text="Convert PC ➜ PS4",
    command=lambda: run_with_progress(
        lambda: pc_to_ps4(
            int(pc_src_var.get().split()[1]),
            int(ps4_dst_var.get().split()[1])
        )
    ),
    width=25, height=2
).pack(pady=10)

root.mainloop()