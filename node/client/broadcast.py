import logging

import requests

from state.node_state import nodeState
from state.transaction import Transaction


def broadcast_transaction_into_network(transaction_request, address_to_skip=None):
    transaction: Transaction = transaction_request["transaction"]

    if transaction not in nodeState.mempool:
        nodeState.mempool.append(transaction)
        nodeState.print_mempool()
    else:
        logging.info("Transaction already in mempool")
        return

    request_to_broadcast = {
        "transaction": transaction.to_dict(),
        "callback": nodeState.get_callback_address()
    }

    send_to_all_peers(request_to_broadcast,address_to_skip, content=transaction)


def broadcast_block_into_network(block_request):
    block = block_request["block"]

    if block not in nodeState.blockchain:
        nodeState.blockchain.append(block)
        logging.info(f"Block added to blockchain: {block}")
    else:
        logging.info("Block already in blockchain")
        return

    request_to_broadcast = {
        "block": block,
        "callback": nodeState.get_callback_address()
    }

    send_to_all_peers(request_to_broadcast, content=block)


def init_handshake(peer):
    logging.info(f"Initiating handshake with peer: {peer}")
    logging.info(f"https://{peer}/handshake")
    try:
        response = requests.post(f"https://{peer}/handshake",
                                 json={"callback": f"{nodeState.node_address}:{nodeState.node_port}"},
                                 verify=nodeState.verify_ssl_cert)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logging.warn("Request timed out")
    except requests.exceptions.ConnectionError:
        logging.warn("Failed to connect to the server")
    except requests.exceptions.HTTPError as http_err:
        logging.warn(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        logging.warn(f"An error occurred: {err}")
    nodeState.add_peer(peer)
    logging.info(f"Handshake complete with peer: {peer}")


def send_to_all_peers(request_body,address_to_skip, content=""):
    to_remove = []
    logging.info(f"Broadcasting message/block: {content} to all peers")
    for peer in nodeState.connected_peers:
        logging.info(f"Peer: {peer}")
        if peer == address_to_skip:
            continue
        try:
            logging.info(f"Broadcasting message/block to peer: {peer}")
            response = requests.post(f"https://{peer}/broadcastTransaction", json=request_body,
                                     verify=nodeState.verify_ssl_cert)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logging.warn("Request timed out")
            to_remove.append(peer)
        except requests.exceptions.ConnectionError:
            logging.warn("Failed to connect to the server")
            to_remove.append(peer)
        except requests.exceptions.HTTPError as http_err:
            logging.warn(f"HTTP error occurred: {http_err}")
            to_remove.append(peer)
        except requests.exceptions.RequestException as err:
            logging.warn(f"An error occurred: {err}")
            to_remove.append(peer)

    for peer in to_remove:
        nodeState.remove_peer(peer)
        logging.warn(f"Removed peer: {peer}, connected peers: {len(nodeState.connected_peers)}")
