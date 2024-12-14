from pydantic import BaseModel

from state.transaction_data import TransactionData


class Transaction(BaseModel):
    signature: str
    data: TransactionData



    def __eq__(self, other):
        return self.message == other.message and self.timestamp == other.timestamp