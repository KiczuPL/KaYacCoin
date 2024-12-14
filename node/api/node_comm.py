import logging

from client.broadcast import broadcast_transaction_into_network, broadcast_block_into_network
from flask_app import flask_app
from flask import request, jsonify

from state.block import Block
from state.node_state import nodeState
from state.transaction import Transaction


@flask_app.route('/block', methods=['GET'])
def get_block():
    params = request.args
    return jsonify(nodeState.blockchain[int(params["index"])].model_dump())


@flask_app.route('/allBlocks', methods=['GET'])
def get_all_blocks():
    return jsonify([block.model_dump() for block in nodeState.blockchain])


@flask_app.route('/broadcastTransaction', methods=['POST'])
def broadcast_transaction():
    logging.info(f"Broadcasting transaction : {request.get_json()}")
    t = request.get_json()
    tr = Transaction(**t["transaction"])
    nodeState.add_transaction_to_mempool(tr)
    broadcast_transaction_into_network({
        "transaction": tr,
        "callback": nodeState.get_callback_address()
    }, address_to_skip=t["callback"])

    return jsonify(success=True)


@flask_app.route('/blockBroadcast', methods=['POST'])
def broadcast_block():
    logging.info(f"Received broadcast block")
    t = request.get_json()
    block: Block = Block(**t["block"])
    try:
        nodeState.append_block(block)
    except ValueError as e:
        logging.error(f"Error appending block: {e}")
        return "Block is invalid"

    broadcast_block_into_network(block, nodeState.get_callback_address(), address_to_skip=t["callback"])

    return "Block broadcasted", 200


@flask_app.route('/handshake', methods=['POST'])
def handshake():
    logging.info(f"Handshake request from {request.remote_addr}")
    address = request.get_json()["callback"]
    if address is not None:
        nodeState.add_peer(address)
    else:
        logging.warn("No callback address provided")
    return jsonify(success=False)
