from typing import List


class TxIn:
    txOutId: str
    txOutIndex: int


class TxOut:
    address: str
    amount: int


class TransactionData:
    txIns: List[TxIn]
    txOuts: List[TxOut]
