import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QMessageBox
from wallet import Wallet

class WalletApp(QWidget):
    def __init__(self):
        super().__init__()

        # Ustawienia okna
        self.setWindowTitle("Cryptocurrency Wallet")
        self.setGeometry(200, 200, 400, 300)

        # Layout główny
        layout = QVBoxLayout()

        # Pole do wpisania nazwy tożsamości
        self.identity_input = QLineEdit(self)
        self.identity_input.setPlaceholderText("Enter identity name")
        layout.addWidget(self.identity_input)

        # Pole do wpisania hasła
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # Przycisk do tworzenia nowej tożsamości
        self.create_button = QPushButton("Create New Identity", self)
        self.create_button.clicked.connect(self.create_identity)
        layout.addWidget(self.create_button)

        # Lista wszystkich tożsamości
        self.identity_list = QListWidget(self)
        layout.addWidget(self.identity_list)

        # Przycisk do wczytania tożsamości
        self.load_button = QPushButton("Load Selected Identity", self)
        self.load_button.clicked.connect(self.load_identity)
        layout.addWidget(self.load_button)

        # Etykieta do wyświetlania informacji o tożsamości
        self.identity_label = QLabel(self)
        layout.addWidget(self.identity_label)

        # Ustawienie głównego layoutu
        self.setLayout(layout)

        # Załadowanie wszystkich zapisanych tożsamości
        self.load_identity_list()

    def create_identity(self):
        identity_name = self.identity_input.text()
        password = self.password_input.text()

        if not identity_name or not password:
            QMessageBox.warning(self, "Input Error", "Both identity name and password are required.")
            return

        wallet = Wallet(identity_name)
        filename = f"{identity_name}.json"
        wallet.save_identity(password, filename)

        QMessageBox.information(self, "Success", f"Identity {identity_name} created successfully!")

        # Odśwież listę tożsamości
        self.load_identity_list()

    def load_identity(self):
        selected_identity = self.identity_list.currentItem()
        if selected_identity is None:
            QMessageBox.warning(self, "Selection Error", "No identity selected.")
            return

        identity_name = selected_identity.text()
        password = self.password_input.text()

        if not password:
            QMessageBox.warning(self, "Input Error", "Password is required to load the identity.")
            return

        try:
            filename = f"{identity_name}.json"
            identity = Wallet.load_identity(password, filename)
            self.identity_label.setText(f"Public Key: {identity['public_key']}\nPrivate Key: {identity['private_key']}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def load_identity_list(self):
        self.identity_list.clear()

        # Wyszukaj wszystkie pliki .json w folderze
        for filename in os.listdir('.'):
            if filename.endswith('.json'):
                identity_name = filename.split('.')[0]
                self.identity_list.addItem(identity_name)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WalletApp()
    window.show()
    sys.exit(app.exec_())
