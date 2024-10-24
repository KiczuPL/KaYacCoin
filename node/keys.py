import logging

from cryptography.hazmat.primitives import serialization


def load_key(private_key_path: str):
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )
    logging.info(f"loaded key from {private_key_path}")
    return private_key
