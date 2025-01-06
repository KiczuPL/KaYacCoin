import logging
from math import log2
import random
from typing import List, Dict

from state.block import Block
from state.transaction import Transaction, create_coinbase
from state.transaction_data import TxOut
from utils.mining import mine_block
from validation.validation import validate_block, validate_transaction


class NodeState:

    def __init__(self):
        self.mode = "INIT"
        self.start_peers = []
        self.connected_peers = []
        self.blockchain_blocks: Dict[str, Block] = {}
        self.blockchain_leaf_blocks: Dict[str, Block] = {}
        # self.orphan_blocks_by_prev_hash: Dict[str, Block] = {} todo: implement later
        self.public_key_hex_str: str | None = None
        self.node_address = None
        self.node_port = None
        self.mempool: List[Transaction] = []
        self.mempool_tx_ins = {}
        self.unspent_transaction_outputs = {}
        self.starting_difficulty = 1
        self.coinbase_amount = 1000
        self.verify_ssl_cert = False
        self.is_mining = True
        self.is_mining_container = {"value": True}
        self.difficulty_update_interval = 150
        self.target_block_time_seconds = 10

    def get_next_mining_base_block(self) -> Block:
        max_index = max([block.data.index for block in self.blockchain_leaf_blocks.values()])
        mx_blocks = [block for block in self.blockchain_leaf_blocks.values() if block.data.index == max_index]
        return random.choice(mx_blocks)

        # return sorted(self.blockchain_leaf_blocks.values(), key=lambda x: (-x.data.index))[0]

    def get_dumped_blockchain(self):
        chain = [block.model_dump() for block in self.blockchain_blocks.values()]
        return sorted(chain, key=lambda x: (x["data"]["index"], x["data"]["timestamp"]))

    def get_block_nth_ancestor(self, block: Block, n: int):
        if n == 0:
            return block
        return self.get_block_nth_ancestor(self.blockchain_blocks[block.data.previous_hash], n - 1)

    def get_difficulty_for_block(self, block: Block):
        if block.data.index == 0:
            return self.starting_difficulty

        parent_block = self.blockchain_blocks[block.data.previous_hash]
        if block.data.index % self.difficulty_update_interval == 0:
            last_recalculated_block = self.get_block_nth_ancestor(block, self.difficulty_update_interval)
            first_block_time = last_recalculated_block.data.timestamp
            last_block_time = parent_block.data.timestamp
            time_diff = last_block_time - first_block_time
            expected_time_diff = self.difficulty_update_interval * self.target_block_time_seconds
            current_difficulty = parent_block.data.difficulty

            multiplier = log2((expected_time_diff / time_diff) + 1)
            new_difficulty = int(multiplier * current_difficulty)

            logging.info(f"New difficulty: {multiplier} * {current_difficulty} = {new_difficulty}")
            if new_difficulty - current_difficulty > 4:
                new_difficulty = current_difficulty + 4
            return new_difficulty

        return parent_block.data.difficulty

    def pause_mining(self):
        self.is_mining = False
        self.is_mining_container["value"] = False
        logging.info("Mining paused")

    def allow_mining(self):
        self.is_mining = True
        logging.info("Mining allowed")

    def resume_mining_if_possible(self):
        self.is_mining_container["value"] = self.is_mining
        logging.info("Mining resumed")

    def get_public_key_hex_str(self):
        return self.public_key_hex_str

    def get_unspent_transaction_output(self, txOutId: str, txOutIndex: int):
        return self.unspent_transaction_outputs.get(f"{txOutId}:{txOutIndex}")

    def add_unspent_transaction_output(self, txOutId: str, txOutIndex: int, txOut: TxOut):
        self.unspent_transaction_outputs[f"{txOutId}:{txOutIndex}"] = txOut

    def create_coinbase_transaction_for_block(self, block: Block):
        coinbase = create_coinbase(self.get_public_key_hex_str(), block.data.index,
                                   self.coinbase_amount)
        return coinbase

    def add_transaction_to_mempool(self, transaction: Transaction):
        if not validate_transaction(transaction, self.unspent_transaction_outputs):
            logging.info("Transaction is invalid")
            raise ValueError("Transaction is invalid")

        if transaction in self.mempool:
            logging.debug("Transaction already in mempool")
            raise ValueError("Transaction already in mempool")

        staged_tx_ins = {}
        for txIn in transaction.data.txIns:
            if f"{txIn.txOutId}:{txIn.txOutIndex}" in self.mempool_tx_ins:
                logging.info("Same transaction input already in mempool")
                raise ValueError("Same transaction input already in mempool")
            staged_tx_ins[f"{txIn.txOutId}:{txIn.txOutIndex}"] = transaction

        self.mempool.append(transaction)
        self.mempool_tx_ins.update(staged_tx_ins)
        logging.debug(f"Transaction added to mempool: {transaction}")

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
        if not self.blockchain_blocks:
            if not block.is_genesis_block():
                raise ValueError("Block is not genesis block")
            self.blockchain_blocks[block.hash] = block
            self.blockchain_leaf_blocks[block.hash] = block
            return

        if block.hash in self.blockchain_blocks:
            raise ValueError("Block already in blockchain")

        if not block.data.previous_hash in self.blockchain_blocks:
            raise ValueError("Invalid block, previous hash does not match any block")

        parent_block = self.blockchain_blocks[block.data.previous_hash]

        if not validate_block(block, self.unspent_transaction_outputs, self.coinbase_amount,
                              self.get_difficulty_for_block(block), parent_block.data.index + 1):
            raise ValueError("Invalid block")
        # self.pause_mining()
        self.blockchain_blocks[block.hash] = block
        self.blockchain_leaf_blocks[block.hash] = block
        if block.data.previous_hash in self.blockchain_leaf_blocks:
            del self.blockchain_leaf_blocks[block.data.previous_hash]
        self.defrag_mempool(block)
        self.update_utxos(block)
        logging.debug(f"Block added to blockchain: {block}")
        # self.allow_mining()

    def defrag_mempool(self, block: Block):
        logging.debug("Defragging mempool")
        self.mempool = [t for t in self.mempool if t not in block.data.transactions]
        self.mempool_tx_ins = {key: value for key, value in self.mempool_tx_ins.items() if
                               value not in block.data.transactions}
        logging.debug("Mempool defragged")

    def create_genesis_block(self):
        logging.info("Creating genesis block")
        first_coinbase = create_coinbase(self.get_public_key_hex_str(), 0,
                                         self.coinbase_amount)

        genesis = mine_block(
            Block.genesis_block(first_coinbase, difficulty=self.starting_difficulty),
            abort_flag_container=self.is_mining_container)
        self.append_block(genesis)

    def load_blockchain(self, blockchain: dict):
        for block in blockchain:
            self.append_block(Block(**block))

    def update_utxos(self, block):
        for transaction in block.data.transactions:
            for txIn in transaction.data.txIns:
                if txIn.txOutId == "0" and txIn.txOutIndex == block.data.index:
                    continue

                logging.info(f"Removing UTXO: {txIn.txOutId}:{txIn.txOutIndex}")
                del self.unspent_transaction_outputs[f"{txIn.txOutId}:{txIn.txOutIndex}"]
            for i, txOut in enumerate(transaction.data.txOuts):
                logging.info(f"Adding UTXO: {transaction.txId}:{i}")
                self.unspent_transaction_outputs[f"{transaction.txId}:{i}"] = txOut


nodeState = NodeState()
