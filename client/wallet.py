import os
import re
import json
from datetime import datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.exceptions import InvalidSignature

def create_message(identity_name: str, message_text: str) -> dict:
    """
    Tworzy wiadomość w formie słownika.
    """
    if not message_text.strip():
        raise ValueError("Wiadomość nie może być pusta.")
    
    message = {
        "identity": identity_name,
        "message": message_text,
        "timestamp": datetime.utcnow().isoformat()  # Czas w formacie ISO 8601
    }
    return message


def serialize_message_to_json(message: dict) -> str:
    """
    Serializuje wiadomość do formatu JSON.
    """
    return json.dumps(message, indent=4)


# Funkcja do sanitacji nazw tożsamości
def sanitize_identity_name(identity_name: str) -> str:
    if len(identity_name) > 50:
        raise ValueError("Nazwa tożsamości jest za długa. Maksymalna długość to 50 znaków.")
    if not re.match(r"^[a-zA-Z0-9_-]+$", identity_name):
        raise ValueError("Nazwa tożsamości zawiera niedozwolone znaki. Dozwolone są tylko litery, cyfry, myślniki i podkreślenia.")
    return identity_name


# Funkcja do wyprowadzenia klucza AES z hasła
def derive_key_from_password(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())


# Funkcja szyfrująca AES-GCM
def encrypt_with_aes_gcm(key: bytes, data: bytes) -> dict:
    nonce = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return {"ciphertext": ciphertext, "nonce": nonce, "tag": encryptor.tag}


# Funkcja deszyfrująca AES-GCM
def decrypt_with_aes_gcm(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


# Funkcja generująca klucz prywatny i zapisująca go w pliku zaszyfrowanym AES-GCM
def generate_key(identity_name: str, passphrase: str):
    sanitize_identity_name(identity_name)

    directory = "keys"
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = os.path.join(directory, f"{identity_name}.pem")
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    salt = os.urandom(16)
    aes_key = derive_key_from_password(passphrase, salt)
    encrypted_data = encrypt_with_aes_gcm(aes_key, private_pem)

    with open(file_path, "wb") as f:
        f.write(salt)
        f.write(encrypted_data["nonce"])
        f.write(encrypted_data["tag"])
        f.write(encrypted_data["ciphertext"])

    return private_key


# Funkcja odczytująca klucz prywatny z zaszyfrowanego pliku
def load_private_key(identity_name: str, passphrase: str):
    sanitize_identity_name(identity_name)

    file_path = os.path.join("keys", f"{identity_name}.pem")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Klucz dla tożsamości {identity_name} nie został znaleziony.")

    with open(file_path, "rb") as f:
        salt = f.read(16)
        nonce = f.read(12)
        tag = f.read(16)
        ciphertext = f.read()

    aes_key = derive_key_from_password(passphrase, salt)
    private_pem = decrypt_with_aes_gcm(aes_key, nonce, ciphertext, tag)

    private_key = serialization.load_pem_private_key(
        private_pem,
        password=None,
        backend=default_backend()
    )

    return private_key


# Funkcja generująca klucz publiczny
def get_public_key(private_key):
    return private_key.public_key()


# Funkcja podpisująca wiadomość
def sign_message(private_key, message: bytes) -> bytes:
    return private_key.sign(message, ec.ECDSA(hashes.SHA256()))


# Funkcja weryfikująca podpis
def verify_signature(public_key, message: bytes, signature: bytes) -> bool:
    try:
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False
    

def decrypt_pem_file(identity_name: str, passphrase: str) -> str:
    """
    Odszyfrowuje plik .pem i zwraca jego zawartość w postaci tekstu.
    """
    sanitize_identity_name(identity_name)

    file_path = os.path.join("keys", f"{identity_name}.pem")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Klucz dla tożsamości {identity_name} nie został znaleziony.")

    with open(file_path, "rb") as f:
        salt = f.read(16)
        nonce = f.read(12)
        tag = f.read(16)
        ciphertext = f.read()

    aes_key = derive_key_from_password(passphrase, salt)
    private_pem = decrypt_with_aes_gcm(aes_key, nonce, ciphertext, tag)

    # Zwróć odszyfrowany plik w formie tekstu
    return private_pem.decode("utf-8")
