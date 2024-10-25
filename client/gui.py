import os
import requests
import tkinter as tk
from tkinter import messagebox
from wallet import generate_key, load_private_key, get_public_key
from cryptography.hazmat.primitives import serialization

class CryptoWalletApp:
    def __init__(self, root):
        # Główne okno aplikacji
        self.root = root
        self.root.title("Crypto Wallet")
        self.root.geometry("500x300")

        # Ustawienie elastycznych wierszy i kolumn dla dynamicznego skalowania
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Ramka centralna, która wyśrodkuje zawartość
        frame_center = tk.Frame(self.root)
        frame_center.grid(row=0, column=0, padx=10, pady=10, sticky="nsew", columnspan=2)

        # Ustawienie elastyczności ramki centralnej
        frame_center.grid_rowconfigure(0, weight=1)
        frame_center.grid_columnconfigure(0, weight=1)

        # Ramka dla sekcji tożsamości
        frame_left = tk.Frame(frame_center)
        frame_left.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

        # Lista tożsamości (pliki .pem)
        tk.Label(frame_left, text="Tożsamości").pack(anchor="w")
        self.identity_listbox = tk.Listbox(frame_left, height=10, width=25)
        self.identity_listbox.pack(pady=5)
        self.load_identities()

        # Ramka dla sekcji operacji (prawa strona)
        frame_right = tk.Frame(frame_center)
        frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Etykieta i pole do wpisania nazwy tożsamości
        tk.Label(frame_right, text="Nazwa tożsamości:").grid(row=0, column=0, sticky="w", padx=5)
        self.identity_name_entry = tk.Entry(frame_right, width=25)
        self.identity_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Etykieta i pole do wpisania hasła
        tk.Label(frame_right, text="Hasło:").grid(row=1, column=0, sticky="w", padx=5)
        self.passphrase_entry = tk.Entry(frame_right, show="*", width=25)
        self.passphrase_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Guziki operacyjne, wyśrodkowane
        self.generate_button = tk.Button(frame_right, text="Generuj tożsamość", command=self.generate_identity)
        self.generate_button.grid(row=2, column=1, padx=5, pady=5)

        self.decrypt_button = tk.Button(frame_right, text="Odszyfruj klucz prywatny", command=self.decrypt_private_key)
        self.decrypt_button.grid(row=3, column=1, padx=5, pady=5)

        self.public_key_button = tk.Button(frame_right, text="Pokaż klucz publiczny", command=self.show_public_key)
        self.public_key_button.grid(row=4, column=1, padx=5, pady=5)

        # Sekcja testowania połączenia z nodem (na dole)
        frame_bottom = tk.Frame(self.root)
        frame_bottom.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        tk.Label(frame_bottom, text="Adres noda:").grid(row=0, column=0, sticky="w", padx=5)
        self.node_address_entry = tk.Entry(frame_bottom, width=40)
        self.node_address_entry.grid(row=0, column=1, padx=5)

        self.test_connection_button = tk.Button(frame_bottom, text="Test", command=self.test_node_connection)
        self.test_connection_button.grid(row=0, column=2, padx=5, pady=5)

    def load_identities(self):
        """Wczytuje listę istniejących tożsamości (plików .pem) z folderu keys."""
        self.identity_listbox.delete(0, tk.END)
        keys_dir = "keys"
        if os.path.exists(keys_dir):
            for identity_file in os.listdir(keys_dir):
                if identity_file.endswith(".pem"):
                    self.identity_listbox.insert(tk.END, identity_file.replace(".pem", ""))

    def generate_identity(self):
        """Generuje nowy klucz prywatny EC i zapisuje go do pliku .pem."""
        identity_name = self.identity_name_entry.get()
        passphrase = self.passphrase_entry.get()

        if not identity_name or not passphrase:
            messagebox.showerror("Błąd", "Nazwa tożsamości i hasło nie mogą być puste!")
            return

        try:
            generate_key(identity_name, passphrase)
            messagebox.showinfo("Sukces", f"Klucz dla {identity_name} został wygenerowany!")
            self.load_identities()  # Odśwież listę tożsamości
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def decrypt_private_key(self):
        """Odszyfrowuje klucz prywatny dla wybranej tożsamości."""
        selected_identity = self.identity_listbox.get(tk.ACTIVE)
        passphrase = self.passphrase_entry.get()

        if not selected_identity or not passphrase:
            messagebox.showerror("Błąd", "Proszę wybrać tożsamość i podać hasło.")
            return

        try:
            private_key = load_private_key(selected_identity, passphrase)
            messagebox.showinfo("Sukces", f"Klucz prywatny został odszyfrowany.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się odszyfrować klucza: {str(e)}")

    def show_public_key(self):
        """Wyświetla klucz publiczny wygenerowany z klucza prywatnego."""
        selected_identity = self.identity_listbox.get(tk.ACTIVE)
        passphrase = self.passphrase_entry.get()

        if not selected_identity or not passphrase:
            messagebox.showerror("Błąd", "Proszę wybrać tożsamość i podać hasło.")
            return

        try:
            private_key = load_private_key(selected_identity, passphrase)
            public_key = get_public_key(private_key)
            messagebox.showinfo("Klucz publiczny", f"{public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wygenerować klucza publicznego: {str(e)}")

    def test_node_connection(self):
        """Testuje połączenie z nodem."""
        node_address = self.node_address_entry.get()
        if not node_address:
            messagebox.showerror("Błąd", "Adres noda nie może być pusty!")
            return

        try:
            response = requests.get(f"https://{node_address}/isAlive", verify=False)
            response.raise_for_status()
            messagebox.showinfo("Sukces", f"Połączenie z nodem {node_address} udane!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się połączyć z nodem: {str(e)}")

# Uruchomienie aplikacji
if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoWalletApp(root)
    root.mainloop()
