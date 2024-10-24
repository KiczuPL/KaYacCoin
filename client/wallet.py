import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature

# Funkcja generująca klucz prywatny i zapisująca go do pliku .pem
def generate_key(identity_name: str, passphrase: str):

    # Generuje klucz prywatny EC i zapisuje go do pliku .pem z nazwą opartą na nazwie tożsamości.
    # Klucz jest szyfrowany hasłem.
    directory = "keys"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Ścieżka do pliku, gdzie nazwa tożsamości staje się nazwą pliku
    file_path = os.path.join(directory, f"{identity_name}.pem")

    # Generowanie klucza prywatnego (krzywa eliptyczna SECP256R1)
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

    # Zapis klucza prywatnego do pliku .pem z szyfrowaniem hasłem
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode())
    )

    # Zapisanie zaszyfrowanego klucza prywatnego do pliku
    with open(file_path, "wb") as f:
        f.write(private_pem)

    return private_key


# Funkcja odczytująca klucz prywatny z pliku i deszyfrująca go hasłem
def load_private_key(identity_name: str, passphrase: str):

    # Wczytuje i odszyfrowuje klucz prywatny z pliku .pem.
    file_path = os.path.join("keys", f"{identity_name}.pem")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Klucz dla tożsamości {identity_name} nie został znaleziony.")

    # Wczytanie i odszyfrowanie klucza prywatnego z pliku .pem
    with open(file_path, "rb") as f:
        encrypted_pem = f.read()

    private_key = serialization.load_pem_private_key(
        encrypted_pem,
        password=passphrase.encode(),
        backend=default_backend()
    )

    return private_key


# Funkcja generująca klucz publiczny na bieżąco z klucza prywatnego
def get_public_key(private_key):
    return private_key.public_key()


# Funkcja podpisująca wiadomość za pomocą klucza prywatnego
def sign_message(private_key, message: bytes) -> bytes:
    signature = private_key.sign(
        message,
        ec.ECDSA(hashes.SHA256())
    )
    return signature


# Funkcja weryfikująca podpis przy użyciu klucza publicznego
def verify_signature(public_key, message: bytes, signature: bytes) -> bool:
    try:
        public_key.verify(
            signature,
            message,
            ec.ECDSA(hashes.SHA256())
        )
        return True
    except InvalidSignature:
        return False
