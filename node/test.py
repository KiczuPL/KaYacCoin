import base64
from idlelib.iomenu import encoding

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey

from key_generator import get_key
from state.transaction_data import TxIn

if []:
    print("sranie")







tx1 = TxIn(txOutId="1", txOutIndex=1)
tx2 = TxIn(txOutId="1", txOutIndex=2)

print(tx1 == tx2)

tx2.txOutIndex = 1
print(tx1 == tx2)

print({tx1, tx2})

key = get_key("node1")
raw = key.public_key().public_bytes(encoding=serialization.Encoding.DER,
                                    format=serialization.PublicFormat.SubjectPublicKeyInfo).hex()
print(raw)

data = "dupadupadupa"

signature = key.sign(data.encode(), ec.ECDSA(hashes.SHA256()))

k = serialization.load_der_public_key(bytes.fromhex(raw), backend=EllipticCurvePublicKey)

print(base64.b64encode(k.public_bytes(encoding=serialization.Encoding.DER, format=serialization.PublicFormat.SubjectPublicKeyInfo)))

print(k.verify(signature, (data+"a").encode(), ec.ECDSA(hashes.SHA256())))

# print(get_key("node1").public_key().public_bytes(encoding=serialization.Encoding.DER, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode())
