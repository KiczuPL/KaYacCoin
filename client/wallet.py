from Crypto.PublicKey import RSA
from encryption import encrypt_identity, decrypt_identity
import json
import os

def generate_key_pair():
    key = RSA.generate(2048)
    private_key = key.export_key(format='PEM')
    public_key = key.publickey().export_key(format='PEM')
    return private_key, public_key

def create_identity(name: str):
    #Creates an identity with a name and generates a key pair.
    private_key, public_key = generate_key_pair()
    identity = {
        'name': name,
        'private_key': private_key.decode('utf-8'),  # Convert bytes to string
        'public_key': public_key.decode('utf-8'),    # Convert bytes to string
    }
    return identity

def save_identity_to_file(identity: dict, password: str, filename: str):
    #Save an encrypted identity to a JSON file with a unique name.
    encrypted_data_b64, salt_b64, init_vector_b64 = encrypt_identity(identity, password)

    # Save encrypted identity to JSON file
    identity_data = {
        'encrypted_data': encrypted_data_b64,
        'salt': salt_b64,
        'init_vector': init_vector_b64,
    }

    # Ensure the filename has a .json extension
    if not filename.endswith('.json'):
        filename += '.json'

    with open(filename, 'w') as file:
        json.dump(identity_data, file)

def load_identity_from_file(filename: str, password: str):
    with open(filename, 'r') as file:
        identity_data = json.load(file)
    return identity_data

def decrypt_identity_from_file(filename: str, password: str):
    identity_data = load_identity_from_file(filename)
    decrypted_identity = decrypt_identity(
        identity_data['encrypted_data'],
        password,
        identity_data['salt'],
        identity_data['init_vector']
    )
    return decrypted_identity