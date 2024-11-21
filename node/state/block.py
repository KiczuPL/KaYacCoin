from pydantic import BaseModel
from state.block_data import BlockData


class Block(BaseModel):
    hash: str
    data: BlockData

    def calculate_hash(self) -> str:
        self.hash = self.data.calculate_hash()
        return self.hash
