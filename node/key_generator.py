from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


def generate_key(path: str):
    private_key = ec.generate_private_key(ec.SECP256R1())

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
        # encryption_algorithm=serialization.BestAvailableEncryption(b"passphrase")
    )

    with open(path, "wb") as f:
        f.write(private_pem)

    return private_key


generate_key("keys/private_key.pem")
