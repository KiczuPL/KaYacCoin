import logging

from state.block import Block
from state.block_data import BlockData


def build_block(index: int, previous_hash: str, timestamp, difficulty: int, nonce: int, transactions: list) -> Block:
    return Block(hash="",
                 data=BlockData(index=index, previous_hash=previous_hash, difficulty=difficulty, timestamp=timestamp,
                                nonce=nonce,
                                transactions=transactions))


def mine_block(block: Block) -> Block:
    while not block.hash.startswith('0' * block.data.difficulty):
        block.data.nonce += 1
        block.hash = block.calculate_hash()
    logging.info(f"Block mined: {block.hash}, nonce: {block.data.nonce}")
    return block