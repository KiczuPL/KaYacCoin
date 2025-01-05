import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from client.wallet import derive_key_from_password, encrypt_with_aes_gcm


def generate_key(path: str) -> ec.EllipticCurvePrivateKey:
    private_key = ec.generate_private_key(ec.SECP256R1())

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    with open(path, "wb") as f:
        f.write(private_pem)

    return private_key


def get_key(node_name: str) -> ec.EllipticCurvePrivateKey:
    try:
        with open(f"../node/keys/{node_name}_key.pem".encode(), "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
    except FileNotFoundError:
        print(f"Generating new key for {node_name}")
        private_key = generate_key(f"../node/keys/{node_name}_key.pem")

    return private_key


# Funkcja generująca klucz prywatny i zapisująca go w pliku zaszyfrowanym AES-GCM
def save_key(identity_name: str, passphrase: str, private_key: ec.EllipticCurvePrivateKey):
    directory = "keys"
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = os.path.join(directory, f"{identity_name}.pem")
    file_path_public_key = os.path.join(directory, f"{identity_name}.pub")

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key_hex = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint
    ).hex()

    salt = os.urandom(16)
    aes_key = derive_key_from_password(passphrase, salt)
    encrypted_data = encrypt_with_aes_gcm(aes_key, private_pem)

    with open(file_path, "wb") as f:
        f.write(salt)
        f.write(encrypted_data["nonce"])
        f.write(encrypted_data["tag"])
        f.write(encrypted_data["ciphertext"])

    with open(file_path_public_key, "w") as f:
        f.write(public_key_hex)

    return private_key


password = "111"
nodes = ["node1", "node2", "node3", "node4"]

for node in nodes:
    private_key = get_key(node)
    save_key(node, password, private_key)


print("DONE")
