import logging

from state.block import Block

def build_block(index: int, previous_hash: str, timestamp: str, nonce: int, transactions: list) -> Block:
    return Block(index=index, previous_hash=previous_hash, timestamp=timestamp, nonce=nonce, transactions=transactions)

def mine_block(block: Block) -> Block:
    while not block.hash.startswith('0'):
        block.nonce += 1
        block.hash = block.calculate_hash()
    logging.info(f"Block mined: {block.hash}, nonce: {block.nonce}")
    return block
