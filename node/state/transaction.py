from pydantic import BaseModel

from state.transaction_data import TransactionData


class Transaction(BaseModel):
    txId: str
    signature: str
    data: TransactionData


    def is_valid(self):
        # walidacja do przeniesienia do osobnego modułu

        return True

    def __eq__(self, other):
        return self.message == other.message and self.timestamp == other.timestamp