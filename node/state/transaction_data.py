import hashlib
from typing import List

from pydantic import BaseModel


class TxIn(BaseModel):
    txOutId: str
    txOutIndex: int

    def __eq__(self, other):
        return self.txOutId == other.txOutId and self.txOutIndex == other.txOutIndex

    def __hash__(self):
        return hash((self.txOutId, self.txOutIndex))


class TxOut(BaseModel):
    address: str
    amount: int

    def __eq__(self, other):
        return self.address == other.address and self.amount == other.amount

    def __hash__(self):
        return hash((self.address, self.amount))


class TransactionData(BaseModel):
    txIns: List[TxIn]
    txOuts: List[TxOut]

    def calculate_hash(self):
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()

