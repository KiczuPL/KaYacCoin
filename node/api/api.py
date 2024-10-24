import logging

from flask_app import flask_app

from state.node_state import nodeState


@flask_app.route('/isAlive', methods=['GET'])
def isAlive():
    return "KaYakCoin Node alive!"


@flask_app.route('/broadcast', methods=['POST'])
def broadcast():
    logging.info(f"Broadcasting message")
    nodeState.broadcast(f"Hellou message from {nodeState.node_address}:{nodeState.node_port}")
    return "Broadcasted message"
