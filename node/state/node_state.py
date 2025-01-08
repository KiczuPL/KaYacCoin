import logging
from math import log2
from typing import List, Dict

from state.block import Block
from state.transaction import Transaction, create_coinbase
from utils.mining import mine_block
from validation.validation import validate_block, validate_transaction


class NodeState:

    def __init__(self):
        self.mode = "INIT"
        self.start_peers = []
        self.connected_peers = []
        self.blockchain_blocks: Dict[str, Block] = {}
        self.blockchain_leaf_blocks: Dict[str, Block] = {}
        self.public_key_hex_str: str | None = None
        self.node_address = None
        self.node_port = None
        self.mempool: List[Transaction] = []
        self.mempool_tx_ins = {}
        self.block_abandance_height_diff = 10
        self.starting_difficulty = 1
        self.coinbase_amount = 1000
        self.is_mining = True
        self.is_mining_container = {"value": True}
        self.difficulty_update_interval = 20
        self.target_block_time_seconds = 10
        self.evil_mode = False
        self.evil_mining_last_block = None

    def get_address_utxos(self, address: str):
        utxos = []
        for key, value in self.get_next_mining_base_block().get_metadata().unspent_transaction_outputs.items():
            if value.address == address:
                utxos.append({"txOutId": key.split(":")[0],
                              "txOutIndex": key.split(":")[1],
                              "amount": value.address})

        return utxos

    def process_stale_blocks(self):
        next_mining_base_block = self.get_next_mining_base_block()
        for block_hash in list(self.blockchain_leaf_blocks.keys()):
            stale_block = self.blockchain_leaf_blocks[block_hash]
            if stale_block.data.index < next_mining_base_block.data.index - self.block_abandance_height_diff:
                logging.info(f"Processing stale block: {stale_block}")
                self.blockchain_leaf_blocks.pop(block_hash)

    def get_next_mining_base_block(self) -> Block:
        next_proper_block = sorted(self.blockchain_leaf_blocks.values(), key=lambda x: (-x.data.index))[0]

        if self.evil_mode and self.evil_mining_last_block is not None and self.evil_mining_last_block.data.index > next_proper_block.data.index - self.block_abandance_height_diff:
            return self.evil_mining_last_block

        return next_proper_block

    def get_dumped_blockchain(self):
        chain = [self.blockchain_blocks[key].model_dump() for key in list(self.blockchain_blocks.keys())]
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

    def create_coinbase_transaction_for_block(self, block: Block):
        coinbase = create_coinbase(self.get_public_key_hex_str(), block.data.index,
                                   self.coinbase_amount)
        return coinbase

    def add_transaction_to_mempool(self, transaction: Transaction):
        if not validate_transaction(transaction,
                                    self.get_next_mining_base_block().get_metadata().unspent_transaction_outputs):
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
            utxos = {f"{block.data.transactions[0].txId}:0": block.data.transactions[0].data.txOuts[0]}
            block.get_metadata().unspent_transaction_outputs = block.get_metadata().unspent_transaction_outputs | utxos
            return

        if block.hash in self.blockchain_blocks:
            raise ValueError("Block already in blockchain")

        if not block.data.previous_hash in self.blockchain_blocks:
            raise ValueError("Invalid block, previous hash does not match any block")

        parent_block = self.blockchain_blocks[block.data.previous_hash]
        block.get_metadata().unspent_transaction_outputs = self.build_block_utxos(block, parent_block)

        if not validate_block(block, self.coinbase_amount,
                              self.get_difficulty_for_block(block), parent_block.data.index + 1):
            raise ValueError("Invalid block")
        # self.pause_mining()
        self.blockchain_blocks[block.hash] = block
        self.blockchain_leaf_blocks[block.hash] = block
        parent_block.get_metadata().children_hashes.append(block.hash)
        if block.data.previous_hash in self.blockchain_leaf_blocks:
            del self.blockchain_leaf_blocks[block.data.previous_hash]
        self.defrag_mempool(block)
        logging.debug(f"Block added to blockchain: {block}")
        # self.allow_mining()
        if self.evil_mode:
            if self.evil_mining_last_block is None:
                self.evil_mining_last_block = block
            elif block.data.index > self.evil_mining_last_block.data.index and \
                    block.data.transactions[0].data.txOuts[0].address == self.public_key_hex_str:
                self.evil_mining_last_block = block
            elif block.data.previous_hash == self.evil_mining_last_block.hash and \
                    block.data.transactions[0].data.txOuts[0].address == self.public_key_hex_str:
                self.evil_mining_last_block = block

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
            miner_config_container=self.is_mining_container)
        self.append_block(genesis)

    def load_blockchain(self, blockchain: dict):
        for block in blockchain:
            self.append_block(Block(**block))

    def build_block_utxos(self, block: Block, parent_block: Block):
        utxos = parent_block.get_metadata().unspent_transaction_outputs.copy()
        for transaction in block.data.transactions:
            for txIn in transaction.data.txIns:
                if txIn.txOutId == "0" and txIn.txOutIndex == block.data.index:
                    continue

                logging.info(f"Removing UTXO: {txIn.txOutId}:{txIn.txOutIndex}")
                del utxos[f"{txIn.txOutId}:{txIn.txOutIndex}"]

            for i, txOut in enumerate(transaction.data.txOuts):
                logging.info(f"Adding UTXO: {transaction.txId}:{i}")
                utxos[f"{transaction.txId}:{i}"] = txOut
        return utxos


nodeState = NodeState()
