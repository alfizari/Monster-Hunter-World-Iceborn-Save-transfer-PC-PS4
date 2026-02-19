import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import mhw as PC
import ps4 as PS4
import threading

def read_file(file_path):

    with open(file_path, 'rb') as f:
        data=bytearray(f.read())

    if not data:
        print('No data found')
        return

    return data

def write_file(data, out_put_path):

    if not data:
        print('No data found to write')
        return
    
    if not out_put_path:
        print('No output path gived')
        return
    
    with open(out_put_path, 'wb') as f:
        f.write(data)

    return

def ps4_to_pc():

    try:

        #first we read pc file
        pc_file_path=filedialog.askopenfilename(title='select your PC save')

        file_name= os.path.basename(pc_file_path)

        pc_data=read_file(pc_file_path)

        #decrypt pc file

        pc_data_decrypted= PC.decrypt_save(pc_data)

        #read ps4 file
        ps4_file_path=filedialog.askopenfilename(title='select your PS4 save' , defaultextension='.dat')

        ps4_data=read_file(ps4_file_path)

        if (
            ps4_data[0x48A] == 0 or
            ps4_data[0x48B] == 0 or
            ps4_data[0x4A4] == 0 or
            ps4_data[0x7B9] == 0
                ):
            # save is alr decrypted
            ps4_data_decrypted=ps4_data[:0x600488] + ps4_data[0x6010C0:]

        else:

            #remove the extra section from ps4 file
            ps4_data = ps4_data[:0x600488] + ps4_data[0x6010C0:]

            #decrypt ps4 file
            ps4_data_decrypted= PS4.decrypt_save(ps4_data)

        #transfer ps4 file to pc

        pc_data_decrypted=bytearray(pc_data_decrypted[:0x3010D8] + ps4_data_decrypted[0x488: 0x488 + 0x61D040] + pc_data_decrypted[0x3010D8+0x61D040:])

        #encrypt pc file

        pc_data_encrypted= PC.encrypt_save(bytearray(pc_data_decrypted))

        #write path

        out_path = filedialog.asksaveasfilename(
        title='Select where to save your PC save',
        initialfile=file_name)

        write_file(pc_data_encrypted, out_path)

        print('save transfered')


    except Exception as e:
        messagebox.showerror("Error", str(e))


def pc_to_ps4():

    try:
        
        DECRYPTED=False
        #read ps4 save
        ps4_path=filedialog.askopenfilename(title='Select your ps4 save')

        ps4_data=read_file(ps4_path)

        # save the extra section 
        add_back = ps4_data[0x600488:0x6010C0]

        if (
            ps4_data[0x48A] == 0 or
            ps4_data[0x48B] == 0 or
            ps4_data[0x4A4] == 0 or
            ps4_data[0x7B9] == 0
                ):
            # save is alr decrypted
            ps4_data_without_extra=ps4_data[:0x600488] + ps4_data[0x6010C0:]

            DECRYPTED = True

        else:

            #remove the extra
            ps4_data_without_extra= ps4_data[:0x600488] + ps4_data[0x6010C0:]

            #decrypt save
            ps4_data_decrypted= PS4.decrypt_save(ps4_data_without_extra)

        #read pc save
        pc_file_path=filedialog.askopenfilename(title='Select your PC save')


        pc_data=read_file(pc_file_path)

        #decrypt pc file

        pc_data_decrypted= PC.decrypt_save(pc_data)

        #transfer to ps4

        ps4_data_decrypted= bytearray(ps4_data_decrypted[:0x488] + pc_data_decrypted[0x3010D8: 0x3010D8+ 0x61D040] + ps4_data_decrypted[0x488+0x61D040:])

        #encrypt ps4 save

        if not DECRYPTED:
            ps4_data_encrypted_without_extra= bytearray(PS4.encrypt_save(ps4_data_decrypted))

            #add the extra section back

            ps4_data_encrypted= ps4_data_encrypted_without_extra[:0x600488] + add_back + ps4_data_encrypted_without_extra[0x600488:]

        else:

            ps4_data_encrypted= ps4_data_decrypted[:0x600488] + add_back + ps4_data_decrypted[0x600488:]



        #write data

        out_path = filedialog.asksaveasfilename(
        title='Select where to save your file',
        initialfile='memory.dat',
        defaultextension='.dat',
        filetypes=[('DAT files', '*.dat'), ('All files', '*.*')]
    )

        write_file(ps4_data_encrypted,out_path)

        print('save transfered')


    except Exception as e:
        messagebox.showerror("Error", str(e))

    return

def run_with_progress(task_function):
    def task():
        try:
            task_function()
            messagebox.showinfo("Success", "Operation completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            progress.stop()

    progress.start(10)  # speed of animation
    threading.Thread(target=task, daemon=True).start()



root = tk.Tk()
root.title("MHW Save Converter")
root.geometry("500x300")
root.resizable(False, False)

progress = ttk.Progressbar(root, mode="indeterminate")
progress.pack(side="bottom", fill="x", padx=10, pady=5)

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# ---- Tab 1: PS4 ➜ PC ----
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text="PS4 ➜ PC")

tk.Label(
    tab1,
    text="Instructions:\n\n"
         "1. Select your PC save (base file)\n"
         "2. Select your PS4 save\n"
         "3. Choose where to save the new PC file",
    justify="left"
).pack(pady=20)

tk.Button(
    tab1,
    text="Convert PS4 ➜ PC",
    command=lambda: run_with_progress(ps4_to_pc),
    width=25,
    height=2
).pack()


# ---- Tab 2: PC ➜ PS4 ----
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="PC ➜ PS4")

tk.Label(
    tab2,
    text="Instructions:\n\n"
         "1. Select your PS4 save\n"
         "2. Select your PC save\n"
         "3. Choose where to save the new PS4 file",
    justify="left"
).pack(pady=20)

tk.Button(
    tab2,
    text="Convert PC ➜ PS4",
    command=lambda: run_with_progress(pc_to_ps4),
    width=25,
    height=2
).pack()

root.mainloop()

