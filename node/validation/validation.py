import logging

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey

from state.block import Block
from state.transaction import Transaction


def validate_block(block: Block, unspent_transaction_outputs: dict, expected_coinbase_amount: int,
                   expected_block_difficulty: int) -> bool:
    if not block.is_hash_valid():
        logging.info("Block hash is invalid")
        return False

    if block.data.difficulty != expected_block_difficulty:
        logging.info("Block difficulty is invalid")
        return False

    coinbase = block.data.transactions[0]
    if not validate_coinbase_transaction(coinbase, expected_coinbase_amount):
        logging.info("Coinbase transaction is invalid")
        return False

    for transaction in block.data.transactions[1:]:
        if not validate_transaction(transaction, unspent_transaction_outputs):
            logging.info("Block contains invalid transaction")
            return False

    all_tx_ins = [txIn for transaction in block.data.transactions for txIn in transaction.data.txIns]
    all_unique_tx_ins = set(all_tx_ins)
    if len(all_tx_ins) != len(all_unique_tx_ins):
        logging.info("Block contains duplicated transaction inputs")
        return False

    return True


def validate_coinbase_transaction(transaction: Transaction, expected_coinbase_amount: int) -> bool:
    data_hash = transaction.data.calculate_hash()

    if transaction.txId != data_hash:
        logging.info("Coinbase transaction hash is invalid")
        return False

    if len(transaction.data.txIns) != 1:
        logging.info("Coinbase transaction has more than one input")
        return False

    if transaction.data.txIns[0].txOutId != "0":
        logging.info("Coinbase transaction input is invalid")
        return False

    if len(transaction.data.txOuts) != 1:
        logging.info("Coinbase transaction has more than one output")
        return False
    if transaction.data.txOuts[0].amount != expected_coinbase_amount:
        logging.info("Coinbase transaction output amount is invalid")
        return False

    try:
        pub_key = serialization.load_der_public_key(bytes.fromhex(transaction.data.txOuts[0].address),
                                                    backend=EllipticCurvePublicKey)
        pub_key.verify(bytes.fromhex(transaction.signature), data_hash.encode(), ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        logging.info("Transaction signature is invalid. ")
        return False

    return True


def validate_transaction(transaction: Transaction, unspent_transaction_outputs: dict) -> bool:
    data_hash = transaction.data.calculate_hash()

    if transaction.txId != data_hash:
        logging.info("Transaction hash is invalid")
        return False

    if len(transaction.data.txIns) == 0:
        logging.info("Transaction has no inputs")
        return False

    if len(transaction.data.txOuts) == 0:
        logging.info("Transaction has no outputs")
        return False

    if len(transaction.data.txIns) != len(set(transaction.data.txIns)):
        logging.info("Transaction inputs are not unique")
        return False

    unique_input_address = set()
    for txIn in transaction.data.txIns:
        uTxO = unspent_transaction_outputs.get(f"{txIn.txOutId}:{txIn.txOutIndex}")
        if uTxO is None:
            logging.info("Transaction input is not unspent or does not exist")
            return False
        unique_input_address.add(uTxO.address)

    if len(unique_input_address) != 1:
        logging.info("Transaction inputs are not coming from same address")
        return False
    sender_address = list(unique_input_address)[0]

    try:
        pub_key = serialization.load_der_public_key(bytes.fromhex(sender_address),
                                                    backend=EllipticCurvePublicKey)
        pub_key.verify(bytes.fromhex(transaction.signature), bytes.fromhex(data_hash), ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        logging.info("Transaction signature is invalid")
        return False

    if sum([txOut.amount for txOut in transaction.data.txOuts]) != sum(
            [unspent_transaction_outputs.get(f"{txIn.txOutId}:{txIn.txOutIndex}") for txIn in
             transaction.data.txIns]):
        logging.info("Transaction output amount is higher than input amount")
        return False

    return True
