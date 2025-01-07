import logging

from flask import request, jsonify, render_template

from client.broadcast import broadcast_transaction_into_network
from flask_app import flask_app
from state.node_state import nodeState
from state.transaction import Transaction


@flask_app.route('/', methods=['GET'])
def show_chain():
    return render_template('index.html')


@flask_app.route('/isAlive', methods=['GET'])
def is_alive():
    return "KaYakCoin Node alive!"


@flask_app.route('/broadcast', methods=['POST'])
def broadcast():
    logging.info(f"Received broadcast message")
    t = request.get_json()
    tr = Transaction(**t)
    nodeState.add_transaction_to_mempool(tr)
    broadcast_transaction_into_network({
        "transaction": tr,
        "callback": nodeState.get_callback_address()
    })
    return "Message broadcasted"


@flask_app.route('/mempool', methods=['GET'])
def get_mempool():
    return jsonify([transaction.model_dump() for transaction in nodeState.mempool])


@flask_app.route('/getBalance', methods=['GET'])
def get_balance():
    params = request.args

    utxos = nodeState.get_address_utxos(params["address"])

    return jsonify({
        "balance": sum([utxo["amount"] for utxo in utxos]),
        "uTxOs": utxos
    })
