import logging

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey

from state.block import Block
from state.node_state import nodeState
from state.transaction import Transaction


def validate_block(block: Block) -> bool:
    if not block.is_hash_valid():
        logging.info("Block hash is invalid")
        return False

    coinbase = block.data.transactions[0]
    if not validate_coinbase_transaction(coinbase):
        logging.info("Coinbase transaction is invalid")
        return False

    for transaction in block.data.transactions[1:]:
        if not validate_transaction(transaction):
            logging.info("Block contains invalid transaction")
            return False

    return True


def validate_coinbase_transaction(transaction: Transaction) -> bool:
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
    if transaction.data.txOuts[0].amount != nodeState.coinbase_amount:
        logging.info("Coinbase transaction output amount is invalid")
        return False

    try:
        pub_key = serialization.load_der_public_key(bytes.fromhex(transaction.data.txOuts[0].address),
                                                    backend=EllipticCurvePublicKey)
        pub_key.verify(bytes.fromhex(transaction.signature), bytes.fromhex(data_hash), ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        logging.info("Transaction signature is invalid")
        return False

    return True


def validate_transaction(transaction: Transaction) -> bool:
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
        uTxO = nodeState.get_unspent_transaction_output(txIn.txOutId, txIn.txOutIndex)
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
            [nodeState.get_unspent_transaction_output(txIn.txOutId, txIn.txOutIndex).amount for txIn in
             transaction.data.txIns]):
        logging.info("Transaction output amount is higher than input amount")
        return False

    return True
