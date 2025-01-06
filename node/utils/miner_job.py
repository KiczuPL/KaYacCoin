import logging
import sys
import time
import random

from client.broadcast import broadcast_block_into_network
from state.node_state import nodeState
from utils.mining import build_block, mine_block


def miner_scheduled_job():
    logging.info("Mining scheduled job")
    if len(nodeState.mempool) > -1 and nodeState.is_mining:
        parent_block = nodeState.get_next_mining_base_block()
        blockchain_length_at_start = parent_block.data.index + 1
        block = build_block(index=blockchain_length_at_start, previous_hash=parent_block.hash,
                            difficulty=0,
                            timestamp=time.time(), nonce=random.getrandbits(32), transactions=[])
        block.data.transactions = [nodeState.create_coinbase_transaction_for_block(block)] + nodeState.mempool
        block.data.difficulty = nodeState.get_difficulty_for_block(block)
        block = mine_block(block, nodeState.is_mining_container)
        if block is None or not nodeState.is_mining or blockchain_length_at_start != nodeState.get_next_mining_base_block().data.index + 1:
            nodeState.resume_mining_if_possible()
            return

        nodeState.append_block(block)
        broadcast_block_into_network(block, nodeState.get_callback_address())
    else:
        logging.info("No transactions in mempool or mining is disabled")
        return
