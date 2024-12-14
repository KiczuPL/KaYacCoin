from typing import List

from pydantic import BaseModel


class TxIn(BaseModel):
    txOutId: str
    txOutIndex: int


class TxOut(BaseModel):
    address: str
    amount: int


class TransactionData(BaseModel):
    txIns: List[TxIn]
    txOuts: List[TxOut]
