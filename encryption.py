from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA512
from Crypto.Util.Padding import pad, unpad
import base64
import json

def encrypt_identity(identity: dict, password: str):
    password = password.encode()
    salt = get_random_bytes(16)
    key = PBKDF2(password, salt, 32, count=1000000, hmac_hash_module=SHA512)
    init_vector = get_random_bytes(16)
    aes = AES.new(key, AES.MODE_CBC, init_vector)
    identity_json = json.dumps(identity)
    padded_data = pad(identity_json.encode(), AES.block_size)
    encrypted_data = aes.encrypt(padded_data)

    return encrypted_data, salt, init_vector

def decrypt_identity(encrypted_data: bytes, password: str, salt: bytes, init_vector: bytes):
    password = password.encode()
    key = PBKDF2(password, salt, 32, count=1000000, hmac_hash_module=SHA512)
    aes = AES.new(key, AES.MODE_CBC, init_vector)
    padded_data = aes.decrypt(encrypted_data)
    identity_json = unpad(padded_data, AES.block_size).decode()
    identity = json.loads(identity_json)

    return identity
