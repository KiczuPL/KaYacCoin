import logging
import time

from client.broadcast import broadcast_block_into_network
from state.node_state import nodeState
from utils.mining import build_block, mine_block


def miner_scheduled_job():
    logging.info("Mining scheduled job")
    if len(nodeState.mempool) > -1 and nodeState.is_mining:
        blockchain_length_at_start = len(nodeState.blockchain)
        block = build_block(index=blockchain_length_at_start, previous_hash=nodeState.blockchain[-1].hash,
                            difficulty=nodeState.get_difficulty_for_block_index(index=blockchain_length_at_start),
                            timestamp=time.time(), nonce=0,
                            transactions=[nodeState.create_signed_coinbase_transaction()] + nodeState.mempool)
        block = mine_block(block, nodeState.is_mining_container)
        if block is None:
            nodeState.resume_mining_if_possible()
            return

        if not nodeState.is_mining or blockchain_length_at_start != len(nodeState.blockchain):
            nodeState.resume_mining_if_possible()
            return
        nodeState.append_block(block)
        broadcast_block_into_network(block, nodeState.get_callback_address())
    else:
        logging.info("No transactions in mempool or mining is disabled")
        return
