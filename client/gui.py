import os
import requests
import tkinter as tk
from tkinter import messagebox
from wallet import generate_key, load_private_key, get_public_key, decrypt_pem_file
from wallet import sanitize_identity_name, create_message, serialize_message_to_json
from cryptography.hazmat.primitives import serialization

class CryptoWalletApp:
    def __init__(self, root):
        # Główne okno aplikacji
        self.root = root
        self.root.title("Crypto Wallet")
        self.root.geometry("500x450")

        # Główna ramka, podzielona na dwie kolumny: operacje (lewo) i lista tożsamości (prawo)
        frame_main = tk.Frame(self.root)
        frame_main.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Kolumna prawa - lista tożsamości
        frame_right = tk.Frame(frame_main)
        frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="ns")
        tk.Label(frame_right, text="Tożsamości").pack(anchor="w")
        self.identity_listbox = tk.Listbox(frame_right, height=20, width=30)
        self.identity_listbox.pack(pady=5, fill="y", expand=True)
        self.load_identities()

        # Kolumna lewa - operacje
        frame_left = tk.Frame(frame_main)
        frame_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        frame_left.grid_columnconfigure(0, weight=1)

        # Pola do wprowadzania nazwy i hasła
        tk.Label(frame_left, text="Nazwa tożsamości:").grid(row=0, column=0, sticky="w", padx=5)
        self.identity_name_entry = tk.Entry(frame_left, width=40)
        self.identity_name_entry.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        tk.Label(frame_left, text="Hasło:").grid(row=2, column=0, sticky="w", padx=5)
        self.passphrase_entry = tk.Entry(frame_left, show="*", width=40)
        self.passphrase_entry.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        # Przycisk do generowania tożsamości
        self.generate_button = tk.Button(frame_left, text="Generuj tożsamość", command=self.generate_identity, width=30)
        self.generate_button.grid(row=4, column=0, padx=5, pady=15)

        # Trzy rzędy przycisków: pokaż klucz publiczny, odszyfruj klucz prywatny, odszyfruj plik PEM
        self.public_key_button = tk.Button(frame_left, text="Pokaż klucz publiczny", command=self.show_public_key, width=30)
        self.public_key_button.grid(row=5, column=0, padx=5, pady=5)

        self.decrypt_button = tk.Button(frame_left, text="Odszyfruj klucz prywatny", command=self.decrypt_private_key, width=30)
        self.decrypt_button.grid(row=6, column=0, padx=5, pady=5)

        self.view_pem_button = tk.Button(frame_left, text="Odszyfruj plik .pem", command=self.view_decrypted_pem, width=30)
        self.view_pem_button.grid(row=7, column=0, padx=5, pady=5)

        # Pole do wprowadzania wiadomości
        tk.Label(frame_left, text="Wiadomość:").grid(row=8, column=0, sticky="w", padx=5)
        self.message_entry = tk.Entry(frame_left, width=40)
        self.message_entry.grid(row=9, column=0, padx=5, pady=5, sticky="w")

        # Przycisk do przetwarzania wiadomości
        self.process_message_button = tk.Button(frame_left, text="Przetwórz wiadomość", command=self.process_message, width=30)
        self.process_message_button.grid(row=10, column=0, padx=5, pady=15)

        # Sekcja testowania połączenia z nodem
        frame_bottom = tk.Frame(self.root)
        frame_bottom.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        frame_bottom.grid_columnconfigure(1, weight=1)

        tk.Label(frame_bottom, text="Adres noda:").grid(row=0, column=0, sticky="w", padx=5)
        self.node_address_entry = tk.Entry(frame_bottom)
        self.node_address_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
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
        """Generuje nowy klucz prywatny EC i zapisuje go do pliku zaszyfrowanego AES-GCM."""
        identity_name = self.identity_name_entry.get()
        passphrase = self.passphrase_entry.get()

        if not identity_name or not passphrase:
            messagebox.showerror("Błąd", "Nazwa tożsamości i hasło nie mogą być puste!")
            return

        try:
            # Sanitacja nazwy tożsamości
            sanitized_identity = sanitize_identity_name(identity_name)

            # Generowanie klucza i zapisywanie go w pliku
            generate_key(sanitized_identity, passphrase)
            messagebox.showinfo("Sukces", f"Klucz dla {sanitized_identity} został wygenerowany!")
            self.load_identities()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wygenerować klucza: {str(e)}")


    def decrypt_private_key(self):
        """Odszyfrowuje klucz prywatny dla wybranej tożsamości."""
        selected_identity = self.identity_listbox.get(tk.ACTIVE)
        passphrase = self.passphrase_entry.get()

        if not selected_identity or not passphrase:
            messagebox.showerror("Błąd", "Proszę wybrać tożsamość i podać hasło.")
            return

        try:
            # Sanitacja nazwy tożsamości
            sanitized_identity = sanitize_identity_name(selected_identity)

            # Odszyfrowanie klucza
            load_private_key(sanitized_identity, passphrase)
            messagebox.showinfo("Sukces", "Klucz prywatny został odszyfrowany.")
        except FileNotFoundError:
            messagebox.showerror("Błąd", f"Klucz dla tożsamości '{selected_identity}' nie istnieje.")
        except ValueError as ve:
            messagebox.showerror("Błąd walidacji", str(ve))
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
            # Sanitacja nazwy tożsamości
            sanitized_identity = sanitize_identity_name(selected_identity)

            # Załaduj klucz prywatny i wygeneruj publiczny
            private_key = load_private_key(sanitized_identity, passphrase)
            public_key = get_public_key(private_key)
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            messagebox.showinfo("Klucz publiczny", public_key_pem.decode())
        except FileNotFoundError:
            messagebox.showerror("Błąd", f"Klucz dla tożsamości '{selected_identity}' nie istnieje.")
        except ValueError as ve:
            messagebox.showerror("Błąd walidacji", str(ve))
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


    def view_decrypted_pem(self):
        """Wyświetla odszyfrowaną zawartość pliku .pem."""
        selected_identity = self.identity_listbox.get(tk.ACTIVE)
        passphrase = self.passphrase_entry.get()

        if not selected_identity or not passphrase:
            messagebox.showerror("Błąd", "Proszę wybrać tożsamość i podać hasło.")
            return

        try:
            # Sanitacja nazwy tożsamości
            sanitized_identity = sanitize_identity_name(selected_identity)

            # Odszyfrowanie pliku .pem
            decrypted_pem = decrypt_pem_file(sanitized_identity, passphrase)
            messagebox.showinfo("Odszyfrowany plik PEM", decrypted_pem)
        except FileNotFoundError:
            messagebox.showerror("Błąd", f"Klucz dla tożsamości '{selected_identity}' nie istnieje.")
        except ValueError as ve:
            messagebox.showerror("Błąd walidacji", str(ve))
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się odszyfrować pliku: {str(e)}")


    def process_message(self):
        """Przetwarza wprowadzoną wiadomość i wyświetla ją jako JSON."""
        selected_identity = self.identity_listbox.get(tk.ACTIVE)
        message_text = self.message_entry.get()
        node_address = self.node_address_entry.get()
        if not node_address:
            messagebox.showerror("Błąd", "Adres noda nie może być pusty!")
            return
        if not selected_identity:
            messagebox.showerror("Błąd", "Proszę wybrać tożsamość.")
            return

        if not message_text.strip():
            messagebox.showerror("Błąd", "Wiadomość nie może być pusta.")
            return

        try:
            # Tworzenie wiadomości
            message = create_message(selected_identity, message_text)

            # Serializacja do JSON
            requests.post(f"https://{node_address}/broadcast", json=message, verify=False)

            json_message = serialize_message_to_json(message)
            # Wyświetlenie wiadomości w formacie JSON
            messagebox.showinfo("Wysłana wiadomość JSON", json_message)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się przetworzyć wiadomości: {str(e)}")


# Uruchomienie aplikacji
if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoWalletApp(root)
    root.mainloop()
