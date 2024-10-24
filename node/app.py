import argparse
import asyncio
import threading

from argparse import Namespace

from keys import load_key

from api.api import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def init_state(args: Namespace):
    nodeState.public_key = load_key("keys/private_key.pem")
    nodeState.mode = args.mode
    nodeState.node_address = args.address
    nodeState.node_port = args.port
    nodeState.start_peers = [args.peer] if args.peer else []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KaYakCoin Node')
    parser.add_argument('--mode', type=str, required=False, help='Mode of operation', default="INIT")
    parser.add_argument('--address', type=str, required=False, help='Address', default="127.0.0.1")
    parser.add_argument('--port', type=int, required=False, help='Port number', default=2000)
    parser.add_argument('--peer', type=str, required=False, help='Peer address')

    args = parser.parse_args()
    init_state(args)

    if args.mode == "JOIN":
        logging.info("Joining network")
        asyncio.run(nodeState.connect_to_start_peers())


    def run_flask_app():
        flask_app.run(host=args.address, port=8080)


    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    logging.info(f"Starting node on address {args.address}:{args.port} with mode: {args.mode}")

    asyncio.run(nodeState.start_socket())
    # start flask app from api.py as async
