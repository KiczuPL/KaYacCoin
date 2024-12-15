import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec

from key_generator import get_key
from state.transaction import Transaction
from state.transaction_data import TransactionData, TxOut, TxIn

node1_key = get_key("node1")

user1_key = get_key("user1")
user2_key = get_key("user2")

user1_public_key_hex = user1_key.public_key().public_bytes(encoding=serialization.Encoding.DER,
                                                           format=serialization.PublicFormat.SubjectPublicKeyInfo).hex()
user2_public_key_hex = user2_key.public_key().public_bytes(encoding=serialization.Encoding.DER,
                                                           format=serialization.PublicFormat.SubjectPublicKeyInfo).hex()
node1_public_key_hex = node1_key.public_key().public_bytes(encoding=serialization.Encoding.DER,
                                                           format=serialization.PublicFormat.SubjectPublicKeyInfo).hex()

print(f"user1_public_key_hex: {user1_public_key_hex}")
print(f"user2_public_key_hex: {user2_public_key_hex}")
print(f"node1_public_key_hex: {node1_public_key_hex}")

transaction_data = TransactionData(
    txIns=[TxIn(txOutId="f9e167cacde8724418d7a158abfc542f2c579597f4c55029ea7920fd9577ad8b", txOutIndex=0)],
    txOuts=[TxOut(address=user1_public_key_hex, amount=100)])

tx_hash = transaction_data.calculate_hash()
print(f"tx_hash: {tx_hash}")
transaction = Transaction(txId=tx_hash, signature=node1_key.sign(tx_hash.encode(), ec.ECDSA(hashes.SHA256())).hex(),
                          data=transaction_data)

requests.post("http://localhost:2003/broadcast", json=transaction.model_dump())



user1_public_key_hex = user1_key.public_key().public_bytes(encoding=serialization.Encoding.DER,
                                                           format=serialization.PublicFormat.SubjectPublicKeyInfo).hex()
requests.get("http://localhost:2001/getBalance?address=" + user1_public_key_hex).json()