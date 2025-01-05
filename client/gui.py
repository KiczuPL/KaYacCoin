import hashlib
import os
import requests
import tkinter as tk
from tkinter import messagebox, Toplevel, simpledialog, ttk

from cryptography.hazmat.primitives.asymmetric import ec

from client.transaction import TxOut, TxIn, TransactionData, Transaction
from wallet import generate_key, load_private_key, get_public_key, decrypt_pem_file, sign_message
from wallet import sanitize_identity_name, create_message, serialize_message_to_json
from cryptography.hazmat.primitives import serialization, hashes
import json
import pyperclip
import base64
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class CryptoWalletApp:
    def __init__(self, root):
        # Główne okno aplikacji
        self.root = root
        self.root.title("Crypto Wallet")
        self.root.geometry("550x450")

        # Słownik na salda tożsamości i UTXO
        self.identity_balances = {}
        self.utxo_data = {}
        self.identity_name_to_pub_key_dict = {}

        # Główna ramka, podzielona na dwie kolumny: operacje (lewo) i lista tożsamości (prawo)
        frame_main = tk.Frame(self.root)
        frame_main.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Kolumna prawa - lista tożsamości
        frame_right = tk.Frame(frame_main)
        frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="ns")
        tk.Label(frame_right, text="Tożsamość - Saldo").pack(anchor="w")
        self.identity_listbox = tk.Listbox(frame_right, height=20, width=40)
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

        # Przycisk do odświeżania sald
        self.refresh_button = tk.Button(frame_left, text="Odśwież salda", command=self.refresh_balances, width=30)
        self.refresh_button.grid(row=5, column=0, padx=5, pady=5)

        # Przycisk do otwarcia okienka transakcji
        self.new_transaction_button = tk.Button(frame_left, text="Nowa Transakcja",
                                                command=lambda: self.open_transaction_window(
                                                    self.identity_listbox.get(tk.ACTIVE).split(" - ")[0],
                                                    load_private_key(
                                                        self.identity_listbox.get(tk.ACTIVE).split(" - ")[0],
                                                        self.passphrase_entry.get())), width=30)
        self.new_transaction_button.grid(row=6, column=0, padx=5, pady=5)

        # Przycisk do wyświetlania klucza publicznego
        self.show_public_key_button = tk.Button(frame_left, text="Pokaż klucz publiczny", command=self.show_public_key, width=30)
        self.show_public_key_button.grid(row=7, column=0, padx=5, pady=5)

        # Sekcja testowania połączenia z nodem
        frame_bottom = tk.Frame(self.root)
        frame_bottom.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        frame_bottom.grid_columnconfigure(1, weight=1)

        tk.Label(frame_bottom, text="Adres noda:").grid(row=0, column=0, sticky="w", padx=5)
        self.node_address_entry = tk.Entry(frame_bottom)
        self.node_address_entry.insert(0, "127.0.0.1:2001")
        self.node_address_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.test_connection_button = tk.Button(frame_bottom, text="Testuj połączenie z nodem", command=self.test_node_connection)
        self.test_connection_button.grid(row=0, column=2, padx=5, pady=5)

    def load_identities(self):
        """Wczytuje listę istniejących tożsamości (plików .pem i .pub) z folderu keys."""
        self.identity_listbox.delete(0, tk.END)
        self.identity_balances.clear()
        self.utxo_data.clear()
        keys_dir = "keys"
        if os.path.exists(keys_dir):
            for identity_file in os.listdir(keys_dir):
                if identity_file.endswith(".pem"):
                    identity_name = identity_file.replace(".pem", "")
                    self.identity_balances[identity_name] = "Nieznane"
                    self.identity_listbox.insert(tk.END, f"{identity_name} - {self.identity_balances[identity_name]}")
                elif identity_file.endswith(".pub"):
                    identity_name = identity_file.replace(".pub", "")
                    with open(os.path.join(keys_dir, identity_file), "r") as f:
                        self.identity_name_to_pub_key_dict[identity_name] = f.read()

    def show_public_key(self):
        """Wyświetla klucz publiczny dla zaznaczonej tożsamości."""
        selected_identity = self.identity_listbox.get(tk.ACTIVE)
        if not selected_identity:
            messagebox.showerror("Błąd", "Proszę wybrać tożsamość z listy!")
            return

        try:
            identity_name = selected_identity.split(" - ")[0]

            with open(f"keys/{identity_name}.pub", "r", encoding="utf-8") as file:
                public_key_hex = file.read()

                # Okno z kluczem publicznym
                public_key_window = Toplevel(self.root)
                public_key_window.title("Klucz Publiczny")
                tk.Label(public_key_window, text="Klucz Publiczny:").pack(pady=5)
                public_key_text = tk.Text(public_key_window, height=5, wrap="word")
                public_key_text.insert("1.0", public_key_hex)
                public_key_text.config(state="disabled")
                public_key_text.pack(padx=10, pady=5)

                def copy_to_clipboard():
                    pyperclip.copy(public_key_hex)
                    messagebox.showinfo("Sukces", "Klucz publiczny skopiowany do schowka!")

                copy_button = tk.Button(public_key_window, text="Kopiuj", command=copy_to_clipboard)
                copy_button.pack(pady=5)

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wyświetlić klucza publicznego: {str(e)}")

    def refresh_balances(self):
        """Odświeża salda dla wszystkich tożsamości."""
        node_address = self.node_address_entry.get()
        if not node_address:
            messagebox.showerror("Błąd", "Adres noda nie może być pusty!")
            return

        progress_window = Toplevel(self.root)
        progress_window.title("Odświeżanie sald")
        progress_window.geometry("300x100")
        tk.Label(progress_window, text="Proszę czekać, trwa odświeżanie sald...").pack(pady=10)
        progress_bar = ttk.Progressbar(progress_window, length=250, mode='determinate')
        progress_bar.pack(pady=10)

        total_identities = len(self.identity_balances)
        progress_step = 100 / total_identities if total_identities else 100

        try:
            for i, identity in enumerate(self.identity_balances.keys()):
                sanitized_identity = sanitize_identity_name(identity)
                public_key_hex = self.identity_name_to_pub_key_dict[sanitized_identity]

                response = requests.get(f"https://{node_address}/getBalance?address={public_key_hex}", verify=False)
                response.raise_for_status()
                response_body = response.json()

                # Pobranie UTXO i segregacja
                sorted_utxos = sorted(response_body['uTxOs'], key=lambda x: x['amount'])
                self.utxo_data[identity] = sorted_utxos  # Zapisanie UTXO w słowniku

                # Aktualizacja salda
                balance = response_body['balance']
                self.identity_balances[identity] = balance
                logging.info(f"Saldo dla {identity}: {balance}, UTXO: {sorted_utxos}")

                # Aktualizacja progress baru
                progress_bar['value'] += progress_step
                progress_window.update_idletasks()

            self.update_identity_listbox()
            messagebox.showinfo("Sukces", "Salda zostały zaktualizowane!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się pobrać sald: {str(e)}")
        finally:
            progress_window.destroy()

    def update_identity_listbox(self):
        """Aktualizuje wyświetlanie tożsamości z saldami."""
        self.identity_listbox.delete(0, tk.END)
        for identity, balance in self.identity_balances.items():
            self.identity_listbox.insert(tk.END, f"{identity} - {balance}")

    def open_transaction_window(self, identity_name, private_key):
        """Otwiera nowe okno do wykonywania transakcji."""
        transaction_window = Toplevel(self.root)
        transaction_window.title("Nowa Transakcja")
        transaction_window.geometry("400x500")

        # Klucz publiczny tożsamości
        tk.Label(transaction_window, text="Klucz publiczny tożsamości:").pack(anchor="w", padx=10, pady=5)
        public_key_entry = tk.Entry(transaction_window)
        public_key_entry.pack(fill="x", padx=10, pady=5)

        # Kwota
        tk.Label(transaction_window, text="Kwota:").pack(anchor="w", padx=10, pady=5)
        amount_entry = tk.Entry(transaction_window)
        amount_entry.pack(fill="x", padx=10, pady=5)

        # Przycisk dodawania tożsamości
        def add_identity():
            public_key = public_key_entry.get().strip()
            amount = amount_entry.get().strip()
            if not public_key or not amount.isdigit() or int(amount) <= 0:
                messagebox.showerror("Błąd", "Podaj prawidłowy klucz publiczny i kwotę!")
                return
            identities_listbox.insert(tk.END, f"{amount} - {public_key}")
            public_key_entry.delete(0, tk.END)
            amount_entry.delete(0, tk.END)

        add_button = tk.Button(transaction_window, text="Dodaj", command=add_identity, width=20)
        add_button.pack(anchor="w", padx=10, pady=15)

        # Lista tożsamości z kwotami
        tk.Label(transaction_window, text="Kwota - klucz publiczny tożsamości:").pack(anchor="w", padx=10, pady=10)
        identities_listbox = tk.Listbox(transaction_window, height=8)
        identities_listbox.pack(fill="x", padx=10, pady=5)

        # Funkcje do usuwania i edycji tożsamości
        def remove_identity():
            selected = identities_listbox.curselection()
            if selected:
                identities_listbox.delete(selected)

        def edit_identity():
            selected = identities_listbox.curselection()
            if not selected:
                messagebox.showerror("Błąd", "Wybierz tożsamość do edycji!")
                return
            selected_value = identities_listbox.get(selected)
            public_key, current_amount = selected_value.split(" - ")
            new_amount = simpledialog.askstring("Edytuj kwotę", f"Nowa kwota dla {public_key}:", initialvalue=current_amount)
            if new_amount and new_amount.isdigit() and int(new_amount) > 0:
                identities_listbox.delete(selected)
                identities_listbox.insert(selected, f"{public_key} - {new_amount}")
            else:
                messagebox.showerror("Błąd", "Podaj prawidłową kwotę!")

        def submit_transaction():
            sum = 0
            transaction_outputs = []
            for entry in identities_listbox.get(0, tk.END):
                s = entry.split(" - ")
                amount = int(s[0])
                public_key = s[1]
                sum += amount
                transaction_outputs.append(
                    TxOut(address=public_key, amount=amount)
                )
            transaction_inputs = []
            for utxo in self.utxo_data[identity_name]:
                sum -= utxo['amount']
                transaction_inputs.append(
                    TxIn(txOutId=utxo['txOutId'],txOutIndex=utxo['txOutIndex'])
                )
                if sum <= 0:
                    break

            if sum < 0:
                transaction_outputs.append(
                    TxOut(address=private_key.public_key().public_bytes(encoding=serialization.Encoding.DER,format=serialization.PublicFormat.SubjectPublicKeyInfo).hex()
                          , amount=-sum)
                )

            transaction_data = TransactionData(txIns=transaction_inputs, txOuts=transaction_outputs)


            data_hash = transaction_data.calculate_hash()  # todo: trzeba się upewnić czy to daje ten sam hash co model_dump_json z onoda

            transaction = Transaction(
                txId=data_hash, signature=private_key.sign(data_hash.encode(), ec.ECDSA(hashes.SHA256())).hex(),
                data=transaction_data
            )

            requests.post(f"https://{self.node_address_entry.get()}/broadcast", json=transaction.model_dump(), verify=False)

            messagebox.showinfo("Sukces", "Wysłano transakcję")

        button_frame = tk.Frame(transaction_window)

        # Przyciski zarządzania tożsamościami
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Usuń zaznaczone", command=remove_identity, width=20).pack(side="top", pady=5)
        tk.Button(button_frame, text="Edytuj kwotę", command=edit_identity, width=20).pack(side="top", pady=5)
        tk.Button(button_frame, text="Wykonaj Transakcję", command=submit_transaction, width=20).pack(side="top", pady=5)
        """command=lambda: messagebox.showinfo("Sukces", "Transakcja wykonana!")"""

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

    def generate_identity(self):
        """Generuje nowy klucz prywatny EC i zapisuje go do pliku zaszyfrowanego AES-GCM."""
        identity_name = self.identity_name_entry.get()
        passphrase = self.passphrase_entry.get()

        if not identity_name or not passphrase:
            messagebox.showerror("Błąd", "Nazwa tożsamości i hasło nie mogą być puste!")
            return

        try:
            sanitized_identity = sanitize_identity_name(identity_name)
            generate_key(sanitized_identity, passphrase)
            messagebox.showinfo("Sukces", f"Klucz dla {sanitized_identity} został wygenerowany!")
            self.load_identities()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wygenerować klucza: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoWalletApp(root)
    root.mainloop()
