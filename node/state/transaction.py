import hashlib

from pydantic import BaseModel

from state.node_state import nodeState
from state.transaction_data import TransactionData, TxOut, TxIn


def create_coinbase(address: str, block_index: int, amount: int):
    transaction_data = TransactionData(txIns=[TxIn(txOutId="0", txOutIndex=block_index)],
                                       txOuts=[TxOut(address=address, amount=amount)])
    return Transaction(txId=transaction_data.calculate_hash(),
                       signature=nodeState.private_key.sign(transaction_data.calculate_hash().encode()).hex(),
                       data=transaction_data)


class Transaction(BaseModel):
    txId: str
    signature: str
    data: TransactionData

    def __eq__(self, other):
        return self.message == other.message and self.timestamp == other.timestamp
