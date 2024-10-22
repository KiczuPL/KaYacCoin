from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA512
from Crypto.Util.Padding import pad, unpad
import base64
import json

def encrypt_identity(identity: dict, password: str):
    password = password.encode()  # Convert password to bytes
    salt = get_random_bytes(16)   # Generate random salt
    key = PBKDF2(password, salt, 32, count=1000000, hmac_hash_module=SHA512)  # Derive key
    init_vector = get_random_bytes(16)  # Generate random initialization vector (IV)

    aes = AES.new(key, AES.MODE_CBC, init_vector)
    identity_json = json.dumps(identity)  # Convert identity dictionary to JSON
    padded_data = pad(identity_json.encode(), AES.block_size)  # Pad JSON data to fit AES block size
    encrypted_data = aes.encrypt(padded_data)  # Encrypt the padded data

    # Base64 encode the binary data for storage/transport
    encrypted_data_b64 = base64.b64encode(encrypted_data).decode('utf-8')
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    init_vector_b64 = base64.b64encode(init_vector).decode('utf-8')

    return encrypted_data_b64, salt_b64, init_vector_b64

def decrypt_identity(encrypted_data_b64: str, password: str, salt_b64: str, init_vector_b64: str):
    password = password.encode()  # Convert password to bytes

    # Decode base64-encoded inputs
    encrypted_data = base64.b64decode(encrypted_data_b64)
    salt = base64.b64decode(salt_b64)
    init_vector = base64.b64decode(init_vector_b64)

    # Derive the key again using PBKDF2
    key = PBKDF2(password, salt, 32, count=1000000, hmac_hash_module=SHA512)
    aes = AES.new(key, AES.MODE_CBC, init_vector)

    # Decrypt and unpad the data
    padded_data = aes.decrypt(encrypted_data)
    identity_json = unpad(padded_data, AES.block_size).decode('utf-8')
    identity = json.loads(identity_json)  # Convert JSON string back to dictionary

    return identity