import logging

from client.broadcast import broadcast_transaction_into_network
from flask_app import flask_app
from flask import request, jsonify

from state.node_state import nodeState


@flask_app.route('/broadcastTransaction', methods=['POST'])
def broadcast_transaction():
    logging.info(f"Broadcasting transaction : {request.get_json()}")
    transaction = request.get_json()
    broadcast_transaction_into_network(transaction)
    return jsonify(success=True)


@flask_app.route('/handshake', methods=['POST'])
def handshake():
    logging.info(f"Handshake request from {request.remote_addr}")
    address = request.get_json()["callback"]
    if address is not None:
        nodeState.add_peer(address)
    else:
        logging.warn("No callback address provided")
    return jsonify(success=False)

