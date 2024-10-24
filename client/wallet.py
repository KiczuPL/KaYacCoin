from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os
import json
from encryption import encrypt_identity, decrypt_identity

class Wallet:
    def __init__(self, identity_name):
        self.identity_name = identity_name
        self.private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())  # Generowanie klucza prywatnego
        self.public_key = self.private_key.public_key()  # Generowanie klucza publicznego na podstawie prywatnego

    def export_private_key(self):
        # Serializowanie klucza prywatnego do formatu PEM
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

    def export_public_key(self):
        # Serializowanie klucza publicznego do formatu PEM
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

    def create_identity(self):
        # Tworzenie tożsamości w postaci słownika
        identity = {
            "identity_name": self.identity_name,
            "private_key": self.export_private_key(),
            "public_key": self.export_public_key()
        }
        return identity

    def save_identity(self, password, filename):
        # Tworzenie tożsamości
        identity = self.create_identity()
        
        # Szyfrowanie tożsamości
        encrypted_data, salt, iv = encrypt_identity(identity, password)
        
        # Zapisanie zaszyfrowanej tożsamości do pliku
        encrypted_identity = {
            'encrypted_data': encrypted_data,
            'salt': salt,
            'iv': iv
        }
        
        with open(filename, 'w') as f:
            json.dump(encrypted_identity, f)

    @staticmethod
    def load_identity(password, filename):
        # Odczyt zaszyfrowanej tożsamości z pliku
        if not os.path.exists(filename):
            raise FileNotFoundError("Tożsamość nie istnieje.")
        
        with open(filename, 'r') as f:
            encrypted_identity = json.load(f)

        encrypted_data = encrypted_identity['encrypted_data']
        salt = encrypted_identity['salt']
        iv = encrypted_identity['iv']

        # Deszyfrowanie tożsamości
        identity = decrypt_identity(encrypted_data, password, salt, iv)
        return identity
