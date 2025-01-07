import logging

from state.block import Block
from state.block_data import BlockData


def build_block(index: int, previous_hash: str, timestamp, difficulty: int, nonce: int, transactions: list) -> Block:
    return Block(hash="",
                 data=BlockData(index=index, previous_hash=previous_hash, difficulty=difficulty, timestamp=timestamp,
                                nonce=nonce,
                                transactions=transactions))


def mine_block(block: Block, abort_flag_container:dict) -> Block | None:
    block.hash = block.calculate_hash()
    while not bin(int(block.hash, 16))[2:].zfill(256).startswith("0" * block.data.difficulty):
        block.data.nonce += 1
        block.hash = block.calculate_hash()
        if not abort_flag_container["value"]:
            logging.info("Mining aborted")
            return None
    logging.info(f"Block {block.index} mined: {block.hash}, nonce: {block.data.nonce}")
    return block
