import logging

import requests

from state.block import Block
from state.node_state import nodeState
from state.transaction import Transaction


def broadcast_transaction_into_network(transaction_request, address_to_skip=None):
    transaction: Transaction = transaction_request["transaction"]

    request_to_broadcast = {
        "transaction": transaction.model_dump(),
        "callback": nodeState.get_callback_address()
    }

    send_to_all_peers(request_to_broadcast, address_to_skip, endpoint="/broadcastTransaction", content=transaction)


def broadcast_block_into_network(block: Block, callback_address, address_to_skip=None):
    request_to_broadcast = {
        "block": block.model_dump(),
        "callback": callback_address
    }

    send_to_all_peers(request_to_broadcast, address_to_skip, endpoint="blockBroadcast", content=block)


def init_handshake(peers):
    for peer in peers:
        logging.info(f"Initiating handshake with peer: {peer}")
        logging.info(f"http://{peer}/handshake")
        try:
            response = requests.post(f"http://{peer}/handshake",
                                     json={"callback": f"{nodeState.node_address}:{nodeState.node_port}"})
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


def send_to_all_peers(request_body, address_to_skip, endpoint, content=""):
    to_remove = []
    logging.debug(f"Broadcasting message/block: {content} to all peers")
    for peer in nodeState.connected_peers:
        logging.debug(f"Peer: {peer}")
        if peer == address_to_skip:
            continue
        try:
            logging.debug(f"Broadcasting message/block to peer: {peer}")
            response = requests.post(f"http://{peer}/{endpoint}", json=request_body,
                                     )
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


def get_block(node_address, index):
    try:
        response = requests.get(f"http://{node_address}/block?index={index}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logging.warn("Request timed out")
    except requests.exceptions.ConnectionError:
        logging.warn("Failed to connect to the server")
    except requests.exceptions.HTTPError as http_err:
        logging.warn(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        logging.warn(f"An error occurred: {err}")
    return None


def get_blockchain(node_address):
    try:
        response = requests.get(f"http://{node_address}/allBlocks")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logging.warn("Request timed out")
    except requests.exceptions.ConnectionError:
        logging.warn("Failed to connect to the server")
    except requests.exceptions.HTTPError as http_err:
        logging.warn(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        logging.warn(f"An error occurred: {err}")
    return None
