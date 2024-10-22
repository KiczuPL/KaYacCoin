import tkinter as tk
from tkinter import messagebox, simpledialog
import os
from wallet import create_identity, save_identity_to_file, decrypt_identity_from_file

class IdentityManager:
    def __init__(self, master):
        self.master = master
        self.master.title("Crypto Identity Manager")

        # Frame for Identity Creation
        self.frame = tk.Frame(self.master)
        self.frame.pack(pady=10)

        self.label = tk.Label(self.frame, text="Enter Identity Name:")
        self.label.pack()

        self.name_entry = tk.Entry(self.frame)
        self.name_entry.pack()

        self.password_label = tk.Label(self.frame, text="Enter Password:")
        self.password_label.pack()

        self.password_entry = tk.Entry(self.frame, show='*')
        self.password_entry.pack()

        self.create_button = tk.Button(self.frame, text="Create Identity", command=self.create_identity)
        self.create_button.pack(pady=5)

        self.list_button = tk.Button(self.frame, text="Load Identities", command=self.load_identities)
        self.list_button.pack(pady=5)

        self.identity_listbox = tk.Listbox(self.master, width=50)
        self.identity_listbox.pack(pady=10)

        self.decrypt_button = tk.Button(self.master, text="Decrypt Selected Identity", command=self.decrypt_identity)
        self.decrypt_button.pack(pady=5)

    def create_identity(self):
        name = self.name_entry.get()
        password = self.password_entry.get()

        if not name or not password:
            messagebox.showerror("Error", "Please provide both name and password.")
            return

        identity = create_identity(name)
        filename = f"{name}.json"
        save_identity_to_file(identity, password, filename)
        messagebox.showinfo("Success", f"Identity '{name}' created and saved.")

        self.name_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.load_identities()  # Refresh the list of identities

    def load_identities(self):
        self.identity_listbox.delete(0, tk.END)  # Clear the listbox
        for file in os.listdir():
            if file.endswith(".json"):
                self.identity_listbox.insert(tk.END, file)

    def decrypt_identity(self):
        selected = self.identity_listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select an identity to decrypt.")
            return

        filename = self.identity_listbox.get(selected[0])
        password = simpledialog.askstring("Input", "Enter password to decrypt identity:", show='*')

        if password:
            try:
                identity = decrypt_identity_from_file(filename, password)
                messagebox.showinfo("Decrypted Identity", f"Name: {identity['name']}\nPublic Key: {identity['public_key']}\nPrivate Key: {identity['private_key']}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = IdentityManager(root)
    root.mainloop()
