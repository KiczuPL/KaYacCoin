import logging

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from state.block import Block
from state.transaction import Transaction


def validate_block(block: Block, expected_coinbase_amount: int, unspent_transaction_outputs: dict,
                   expected_block_difficulty: int, expected_index: int) -> bool:
    if block.data.index != expected_index:
        logging.info("Block index is invalid")
        return False

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

    if validate_pub_key_str(transaction.data.txOuts[0].address) is False:
        logging.info("Coinbase transaction output address is invalid")
        return False

    if transaction.signature != "":
        logging.info("Coinbase should have an empty signature")
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
    transaction_inputs_txids = []
    for txIn in transaction.data.txIns:
        uTxO = unspent_transaction_outputs.get(f"{txIn.txOutId}:{txIn.txOutIndex}")
        if uTxO is None:
            logging.info("Transaction input is already spent or does not exist")
            return False
        if txIn.txOutId in transaction_inputs_txids:
            logging.info(f"Utxo {txIn.txOutId} is already used in this transaction")
            return False
        transaction_inputs_txids.append(txIn.txOutId)
        unique_input_address.add(uTxO.address)

    if len(unique_input_address) != 1:
        logging.info("Transaction inputs are not coming from same address")
        return False
    sender_address = list(unique_input_address)[0]

    if validate_pub_key_str(sender_address) is False:
        logging.info("Transaction input address is invalid")
        return False

    try:
        pub_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), bytes.fromhex(sender_address))
        pub_key.verify(bytes.fromhex(transaction.signature), data_hash.encode(), ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        logging.info("Transaction signature is invalid")
        return False

    if sum([txOut.amount for txOut in transaction.data.txOuts]) != sum(
            [unspent_transaction_outputs.get(f"{txIn.txOutId}:{txIn.txOutIndex}").amount for txIn in
             transaction.data.txIns]):
        logging.info("Transaction output amount does not match input amount")
        return False

    return True

def validate_pub_key_str(public_key_str: str) -> bool:
    try:
        if len(public_key_str) != 66 or public_key_str[:2] not in ["02", "03"]:
            return False
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), bytes.fromhex(public_key_str))
        return True
    except ValueError:
        return False
