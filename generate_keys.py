import logging
import os

from client.wallet import derive_key_from_password, encrypt_with_aes_gcm
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

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

def get_pub_key_hex_str(node_name: str) -> str:
    try:
        with open(f"keys/{node_name}_key.pub".encode(), "rb") as f:
            pub_key = f.read().decode()
    except FileNotFoundError:
        logging.error("Public key not found")
        raise FileNotFoundError(f"Public key for {node_name} not found")

    return pub_key


def get_key(node_name: str, dir_str: str) -> ec.EllipticCurvePrivateKey:
    try:
        with open(f"{dir_str}/{node_name}_key.pem".encode(), "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
    except FileNotFoundError:
        private_key = generate_key(f"{dir_str}/{node_name}_key.pem")

    return private_key


def save_key(identity_name: str, passphrase: str, private_key: ec.EllipticCurvePrivateKey, dir_str: str):
    if not os.path.exists(dir_str):
        os.makedirs(dir_str)

    file_path = os.path.join(dir_str, f"{identity_name}.pem")
    file_path_public_key = os.path.join(dir_str, f"{identity_name}.pub")

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

client_key_dir = "client/keys"
node_key_dir = "node/keys"

password = "111"
nodes = ["node1", "node2", "node3", "node4"]

for node in nodes:
    priv_key = get_key(node, client_key_dir)
    save_key(node, password, priv_key, client_key_dir)
    with open(f"{node_key_dir}/{node}_key.pub", "w") as f:
        f.write(priv_key.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        ).hex())

print("DONE")
