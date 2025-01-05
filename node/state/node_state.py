import logging
from math import log2
from typing import List

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey

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
        self.blockchain: List[Block] = []
        self.private_key: EllipticCurvePrivateKey | None = None
        self.node_id = None
        self.node_address = None
        self.node_port = None
        self.mempool: List[Transaction] = []
        self.mempool_tx_ins = {}
        self.unspent_transaction_outputs = {}
        self.starting_difficulty = 17
        self.coinbase_amount = 1000
        self.verify_ssl_cert = False
        self.is_mining = True
        self.is_mining_container = {"value": True}
        self.difficulty_update_interval = 10
        self.target_block_time_seconds = 30

    def get_difficulty_for_block_index(self, index: int):
        if index == 0:
            return self.starting_difficulty

        if index % self.difficulty_update_interval == 0:
            first_block_time = self.blockchain[-self.difficulty_update_interval].data.timestamp
            last_block_time = self.blockchain[-1].data.timestamp
            time_diff = last_block_time - first_block_time
            expected_time_diff = self.difficulty_update_interval * self.target_block_time_seconds
            current_difficulty = self.blockchain[-1].data.difficulty

            multiplier = log2((expected_time_diff / time_diff) + 1)
            new_difficulty = int(multiplier * current_difficulty)

            logging.info(f"New difficulty: {multiplier} * {current_difficulty} = {new_difficulty}")
            if new_difficulty - current_difficulty > 4:
                new_difficulty = current_difficulty + 4
            return new_difficulty

        return self.blockchain[-1].data.difficulty

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
        return self.private_key.public_key().public_bytes(encoding=serialization.Encoding.X962,
                                                          format=serialization.PublicFormat.CompressedPoint).hex()

    def get_unspent_transaction_output(self, txOutId: str, txOutIndex: int):
        return self.unspent_transaction_outputs.get(f"{txOutId}:{txOutIndex}")

    def add_unspent_transaction_output(self, txOutId: str, txOutIndex: int, txOut: TxOut):
        self.unspent_transaction_outputs[f"{txOutId}:{txOutIndex}"] = txOut

    def create_coinbase_transaction(self):
        coinbase = create_coinbase(self.get_public_key_hex_str(), self.blockchain[-1].data.index + 1,
                                   self.coinbase_amount)
        return coinbase

    def add_transaction_to_mempool(self, transaction: Transaction):
        if not validate_transaction(transaction, self.unspent_transaction_outputs):
            logging.info("Transaction is invalid")
            raise ValueError("Transaction is invalid")

        if transaction not in self.mempool:
            self.mempool.append(transaction)
            logging.debug(f"Transaction added to mempool: {transaction}")
        else:
            logging.debug("Transaction already in mempool")

        for txIn in transaction.data.txIns:
            if f"{txIn.txOutId}:{txIn.txOutIndex}" in self.mempool_tx_ins:
                logging.info("Same transaction input already in mempool")
                raise ValueError("Same transaction input already in mempool")
            self.mempool_tx_ins[f"{txIn.txOutId}:{txIn.txOutIndex}"] = transaction

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

        if not validate_block(block, self.unspent_transaction_outputs, self.coinbase_amount,
                              self.get_difficulty_for_block_index(block.data.index)):
            raise ValueError("Invalid block")
        self.pause_mining()
        self.blockchain.append(block)
        self.defrag_mempool()
        self.update_utxos(block)
        logging.debug(f"Block added to blockchain: {block}")
        self.allow_mining()

    def defrag_mempool(self):
        logging.debug("Defragging mempool")
        self.mempool = [t for t in self.mempool if t not in self.blockchain[-1].data.transactions]
        self.mempool_tx_ins = {key: value for key, value in self.mempool_tx_ins.items() if
                               value not in self.blockchain[-1].data.transactions}
        logging.debug("Mempool defragged")

    def create_genesis_block(self):
        logging.info("Creating genesis block")
        first_coinbase = create_coinbase(self.get_public_key_hex_str(), 0,
                                         self.coinbase_amount)

        genesis = mine_block(
            Block.genesis_block(first_coinbase, difficulty=self.get_difficulty_for_block_index(index=0)),
            abort_flag_container=self.is_mining_container)
        self.blockchain.append(genesis)

    def load_blockchain(self, blockchain: dict):
        self.blockchain = [Block(**block) for block in blockchain]

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
