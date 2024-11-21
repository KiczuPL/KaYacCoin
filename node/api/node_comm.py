import logging

from client.broadcast import broadcast_transaction_into_network
from flask_app import flask_app
from flask import request, jsonify

from state.node_state import nodeState
from state.transaction import Transaction


@flask_app.route('/broadcastTransaction', methods=['POST'])
def broadcast_transaction():
    logging.info(f"Broadcasting transaction : {request.get_json()}")
    t = request.get_json()

    broadcast_transaction_into_network({
        "transaction": Transaction(**t["transaction"]),
        "callback": nodeState.get_callback_address()
    }, address_to_skip=t["callback"])

    return jsonify(success=True)

@flask_app.route('/blockBroadcast', methods=['POST'])
def broadcast_block():
    logging.info(f"Received broadcast message")
    t = request.get_json()
    broadcast_transaction_into_network({
        "transaction": t,
        "callback": nodeState.get_callback_address()
    })
    return "Block broadcasted"


@flask_app.route('/handshake', methods=['POST'])
def handshake():
    logging.info(f"Handshake request from {request.remote_addr}")
    address = request.get_json()["callback"]
    if address is not None:
        nodeState.add_peer(address)
    else:
        logging.warn("No callback address provided")
    return jsonify(success=False)

