import logging

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

def get_key(node_name: str) -> ec.EllipticCurvePrivateKey:
    try:
        with open(f"keys/{node_name}_key.pem".encode(), "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
    except FileNotFoundError:
        private_key = generate_key(f"keys/{node_name}_key.pem")

    return private_key



def get_pub_key_hex_str(node_name: str) -> str:
    try:
        with open(f"keys/{node_name}_key.pub".encode(), "rb") as f:
            pub_key = f.read().decode()
    except FileNotFoundError:
        logging.error("Public key not found")
        raise FileNotFoundError(f"Public key for {node_name} not found")

    return pub_key



