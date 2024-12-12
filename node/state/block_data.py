from pydantic import BaseModel
from typing import List
import hashlib

from state.transaction import Transaction


class BlockData(BaseModel):
    index: int
    previous_hash: str
    difficulty: int
    timestamp: float
    nonce: int
    transactions: List[Transaction]

    def calculate_hash(self):
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()
