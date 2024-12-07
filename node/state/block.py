import time

from pydantic import BaseModel

from state.block_data import BlockData
from state.transaction import Transaction


class Block(BaseModel):
    hash: str
    data: BlockData

    def calculate_hash(self) -> str:
        self.hash = self.data.calculate_hash()
        return self.hash

    def is_valid(self) -> bool:
        return self.hash == self.calculate_hash()

    def is_genesis_block(self) -> bool:
        return self.data.index == 0 and self.data.previous_hash == "0"

    @staticmethod
    def genesis_block():
        genesis_data = BlockData(index=0, previous_hash="0", timestamp=time.time(), nonce=0,
                                 transactions=[Transaction(message="And so it began", timestamp=time.time())])

        return Block(hash=genesis_data.calculate_hash(), data=genesis_data)
