import logging
import time

from client.broadcast import broadcast_block_into_network
from state.block import Block
from state.block_data import BlockData
from state.node_state import nodeState


def build_block(index: int, previous_hash: str, timestamp, nonce: int, transactions: list) -> Block:
    return Block(hash="", data=BlockData(index=index, previous_hash=previous_hash, timestamp=timestamp, nonce=nonce,
                                         transactions=transactions))


def mine_block(block: Block) -> Block:
    while not block.hash.startswith('000'):
        block.data.nonce += 1
        block.hash = block.calculate_hash()
    logging.info(f"Block mined: {block.hash}, nonce: {block.data.nonce}")
    return block


def miner_scheduled_job():
    logging.info("Mining scheduled job")
    if len(nodeState.mempool) > 0:
        block = build_block(index=len(nodeState.blockchain), previous_hash=nodeState.blockchain[-1].hash,
                            timestamp=time.time(), nonce=0, transactions=list(nodeState.mempool))
        block = mine_block(block)
        broadcast_block_into_network(block, nodeState.get_callback_address())
        nodeState.append_block(block)
    else:
        logging.info("No transactions in mempool")
        return
