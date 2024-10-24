import argparse

from argparse import Namespace
from time import sleep

from cryptography.hazmat.primitives import serialization

from client.broadcast import init_handshake
from keys import load_key

from api.node_comm import *
from api.client_comm import *

from state.node_state import nodeState

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def init_state(args: Namespace):
    nodeState.private_key = load_key("keys/private_key.pem")
    nodeState.mode = args.mode
    nodeState.node_address = args.address
    nodeState.node_port = args.port
    nodeState.start_peers = [args.peer] if args.peer else []
    nodeState.node_id = nodeState.private_key.public_key().public_bytes(encoding=serialization.Encoding.DER,
                                                                        format=serialization.PublicFormat.SubjectPublicKeyInfo).hex()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KaYakCoin Node')
    parser.add_argument('--mode', type=str, required=False, help='Mode of operation', default="INIT")
    parser.add_argument('--address', type=str, required=False, help='Address', default="127.0.0.1")
    parser.add_argument('--port', type=int, required=False, help='Port number', default=2000)
    parser.add_argument('--peer', type=str, required=False, help='Peer address')

    args = parser.parse_args()
    init_state(args)

    logging.info(f"Starting node on address {args.address}:{args.port} with mode: {args.mode}")

    if args.mode == "JOIN":
        logging.info("Joining network")
        init_handshake(args.peer)

    flask_app.run(host=args.address, port=args.port, ssl_context='adhoc')
