import base64
import time
from idlelib.iomenu import encoding
from idlelib.pyparse import trans
from time import sleep

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey

from key_generator import get_key
from state.transaction import create_coinbase

hash = "00ff"
print(bin(int(hash, 16))[2:].zfill(len(hash)*4))


print(time.time())
sleep(5)

print(time.time())



if []:
    print("sranie")

key = get_key("node1")
raw = key.public_key().public_bytes(encoding=serialization.Encoding.DER,
                                    format=serialization.PublicFormat.SubjectPublicKeyInfo).hex()


pub_key_hex = key.public_key().public_bytes(encoding=serialization.Encoding.DER,format=serialization.PublicFormat.SubjectPublicKeyInfo).hex()

transaction = create_coinbase(pub_key_hex, 0, 1000)

hash = transaction.data.calculate_hash()

pub_key = serialization.load_der_public_key(bytes.fromhex(transaction.data.txOuts[0].address),
                                                    backend=EllipticCurvePublicKey)

signature = key.sign(transaction.txId.encode(), ec.ECDSA(hashes.SHA256())).hex()

print(signature)
print(transaction.data.calculate_hash())

try:
    key.public_key().verify(bytes.fromhex(signature), transaction.data.calculate_hash().encode(), ec.ECDSA(hashes.SHA256()))
    print("OK")
except Exception as e:
    pass



col = {}


col["a:1"] = transaction

print(col)

for key,value in col.items():
    print(value)















