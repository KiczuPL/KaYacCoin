import logging
from typing import List

from state.block import Block
from state.transaction import Transaction
from state.transaction_data import TxOut
from utils.mining import mine_block
from validation.validation import validate_block


class NodeState:

    def __init__(self):
        self.mode = "INIT"
        self.start_peers = []
        self.connected_peers = []
        self.blockchain: List[Block] = []
        self.private_key = None
        self.node_id = None
        self.node_address = None
        self.node_port = None
        self.mempool: List[Transaction] = []
        self.unspent_transaction_outputs = {}
        self.difficulty = 3
        self.coinbase_amount = 1000
        self.verify_ssl_cert = False

    def get_unspent_transaction_output(self, txOutId: str, txOutIndex: int):
        return self.unspent_transaction_outputs.get(f"{txOutId}:{txOutIndex}")

    def add_unspent_transaction_output(self, txOutId: str, txOutIndex: int, txOut: TxOut):
        self.unspent_transaction_outputs[f"{txOutId}:{txOutIndex}"] = txOut

    def create_coinbase_transaction(self, address_hex: str):
        return create_coinbase(self.blockchain[-1].data.index + 1, self.coinbase_amount)

    def add_transaction_to_mempool(self, transaction: Transaction):
        if transaction not in self.mempool:
            self.mempool.append(transaction)
            logging.info(f"Transaction added to mempool: {transaction}")
        else:
            logging.info("Transaction already in mempool")

    def add_peer(self, peer):
        if peer in self.connected_peers:
            logging.info(f"Peer {peer} already connected")
            return
        self.connected_peers.append(peer)
        logging.info(f"Added peer: {peer}, connected peers: {len(self.connected_peers)}")

    def remove_peer(self, peer):
        if peer not in self.connected_peers:
            logging.info(f"Peer {peer} not connected")
            return
        self.connected_peers.remove(peer)
        logging.info(f"Removed peer: {peer}, connected peers: {len(self.connected_peers)}")

    def get_callback_address(self):
        return f"{self.node_address}:{self.node_port}"

    def print_mempool(self):
        logging.info(f"MemPool: {self.mempool}")

    def append_block(self, block: Block):
        if len(self.blockchain) == 0:
            if not block.is_genesis_block():
                raise ValueError("Block is not genesis block")
            self.blockchain.append(block)

        if len(self.blockchain) > block.data.index:
            raise ValueError("Block already in blockchain")

        if block.data.index != len(self.blockchain):
            raise ValueError("Block is not next in sequence")

        if not block.data.previous_hash == self.blockchain[-1].hash:
            raise ValueError("Invalid block, hash does not match previous block")

        if not validate_block(block):
            raise ValueError("Invalid block")

        self.blockchain.append(block)
        self.defrag_mempool()
        logging.info(f"Block added to blockchain: {block}")

    def defrag_mempool(self):
        logging.info("Defragging mempool")
        self.mempool = [t for t in self.mempool if t not in self.blockchain[-1].data.transactions]
        logging.info("Mempool defragged")

    def create_genesis_block(self):
        logging.info("Creating genesis block")
        genesis = mine_block(Block.genesis_block())
        self.blockchain.append(genesis)

    def load_blockchain(self, blockchain: dict):
        self.blockchain = [Block(**block) for block in blockchain]


nodeState = NodeState()
