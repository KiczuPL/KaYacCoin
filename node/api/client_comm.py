import logging

from flask import request, jsonify

from client.broadcast import broadcast_transaction_into_network
from flask_app import flask_app
from state.node_state import nodeState
from state.transaction import Transaction


@flask_app.route('/isAlive', methods=['GET'])
def is_alive():
    return "KaYakCoin Node alive!"


@flask_app.route('/broadcast', methods=['POST'])
def broadcast():
    logging.info(f"Received broadcast message")
    t = request.get_json()

    broadcast_transaction_into_network({
        "transaction": Transaction(**t),
        "callback": nodeState.get_callback_address()
    })
    return "Message broadcasted"


@flask_app.route('/mempool', methods=['GET'])
def get_mempool():
    return jsonify([transaction.model_dump() for transaction in nodeState.mempool])
