import logging
import time

from client.broadcast import broadcast_block_into_network
from state.node_state import nodeState
from utils.mining import build_block, mine_block


def miner_scheduled_job():
    logging.info("Mining scheduled job")
    if len(nodeState.mempool) > 0:
        block = build_block(index=len(nodeState.blockchain), previous_hash=nodeState.blockchain[-1].hash,
                            difficulty=nodeState.difficulty,
                            timestamp=time.time(), nonce=0, transactions=list(nodeState.mempool))
        block = mine_block(block)
        nodeState.append_block(block)
        broadcast_block_into_network(block, nodeState.get_callback_address())
    else:
        logging.info("No transactions in mempool")
        return
