import logging

import requests

from state.node_state import nodeState


def broadcast_transaction_into_network(transaction_request):
    transaction = transaction_request["transaction"]
    request_to_broadcast = {
        "transaction": transaction,
        "callback": nodeState.get_callback_address()
    }
    to_remove = []
    if transaction not in nodeState.mempool:
        nodeState.mempool.append(transaction)
        nodeState.print_mempool()
    else:
        logging.info("Transaction already in mempool")
        return

    for peer in nodeState.connected_peers:
        if peer == transaction_request["callback"]:
            continue
        try:
            logging.info(f"Broadcasting message: {transaction} to peer: {peer}")
            response = requests.post(f"https://{peer}/broadcastTransaction", json=request_to_broadcast,
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
