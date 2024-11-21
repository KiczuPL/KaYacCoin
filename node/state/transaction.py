from pydantic import BaseModel


class Transaction(BaseModel):
    message: str
    timestamp: float

    def __eq__(self, other):
        return self.message == other.message and self.timestamp == other.timestamp