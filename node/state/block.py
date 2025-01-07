import time
from typing import List

from pydantic import BaseModel, PrivateAttr

from state.block_data import BlockData
from state.transaction import Transaction

class BlockMetadata:
    children_hashes: List[str] = []
    unspent_transaction_outputs = {}

class Block(BaseModel):
    hash: str
    data: BlockData
    _metadata: BlockMetadata = PrivateAttr(default_factory=BlockMetadata)

    def get_metadata(self) -> BlockMetadata:
        return self._metadata

    def calculate_hash(self) -> str:
        self.hash = self.data.calculate_hash()
        return self.hash

    def is_hash_valid(self) -> bool:
        hash_binary = bin(int(self.hash, 16))[2:].zfill(256)
        return self.hash == self.calculate_hash() and hash_binary.startswith("0" * self.data.difficulty)

    def is_genesis_block(self) -> bool:
        return self.data.index == 0 and self.data.previous_hash == "0"

    @staticmethod
    def genesis_block(coinbase_transaction: Transaction, difficulty: int) -> 'Block':
        genesis_data = BlockData(index=0, previous_hash="0", difficulty=difficulty, timestamp=time.time(), nonce=0,
                                 transactions=[coinbase_transaction])

        return Block(hash=genesis_data.calculate_hash(), data=genesis_data)
