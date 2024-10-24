import logging

from flask import request, jsonify

from client.broadcast import broadcast_transaction_into_network
from flask_app import flask_app
from state.node_state import nodeState


@flask_app.route('/isAlive', methods=['GET'])
def is_alive():
    return "KaYakCoin Node alive!"


@flask_app.route('/broadcast', methods=['POST'])
def broadcast():
    logging.info(f"Broadcasting message")
    t = request.get_json()
    broadcast_transaction_into_network({
        "transaction": t,
        "callback": nodeState.get_callback_address()
    })
    return "Broadcasted message"


@flask_app.route('/mempool', methods=['GET'])
def get_mempool():
    return jsonify(nodeState.mempool)
