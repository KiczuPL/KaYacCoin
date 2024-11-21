from pydantic import BaseModel


class Transaction(BaseModel):
    message: str

    def to_dict(self):
        return {
            "message": self.message
        }