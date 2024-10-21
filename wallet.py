import json
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from encryption import encrypt_identity

def generate_key_pair() -> tuple:
    """Generate an RSA key pair."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    public_key = private_key.public_key()
    
    # Use PKCS8 format for the private key
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,  # You can also use PKCS8 if needed
        encryption_algorithm=serialization.NoEncryption()  # No encryption on private key bytes
    )
    
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    
    return private_key_bytes, public_key_bytes


def create_identity(name: str) -> dict:
    """Creates an identity with a name and generates a key pair."""
    private_key, public_key = generate_key_pair()
    
    identity = {
        "name": name,
        "public_key": base64.b64encode(public_key).decode('utf-8'),  # Encode to Base64
        "private_key": base64.b64encode(private_key).decode('utf-8')  # Encode to Base64
    }
    
    return identity

def save_identity_to_file(identity: dict, password: str, filename: str) -> None:
    """Encrypts the identity and saves it to a JSON file."""
    encrypted_data, salt, init_vector = encrypt_identity(identity, password)

    # Create the JSON structure
    identity_json = {
        "encrypted_data": base64.b64encode(encrypted_data).decode('utf-8'),  # Base64 encode encrypted data
        "salt": base64.b64encode(salt).decode('utf-8'),  # Base64 encode salt
        "iv": base64.b64encode(init_vector).decode('utf-8')  # Base64 encode IV
    }

    # Serialize the identity JSON and save to a file
    with open(filename, 'w') as json_file:
        json.dump(identity_json, json_file, indent=4)