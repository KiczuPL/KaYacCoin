import logging

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey

from state.node_state import nodeState
from state.transaction import Transaction


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
