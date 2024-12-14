import argparse
from argparse import Namespace

from apscheduler.schedulers.background import BackgroundScheduler
from cryptography.hazmat.primitives import serialization

from client.broadcast import init_handshake, get_blockchain
from key_generator import get_key

from api.client_comm import *
from api.node_comm import *
from api.client_comm import *

from state.node_state import nodeState
from utils.miner_job import miner_scheduled_job

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def init_state(args: Namespace):
    nodeState.private_key = get_key(args.nodename)
    nodeState.mode = args.mode
    nodeState.node_address = args.address
    nodeState.node_port = args.port
    nodeState.start_peers = [args.peer] if args.peer else []
    nodeState.node_id = nodeState.private_key.public_key().public_bytes(encoding=serialization.Encoding.DER,
                                                                        format=serialization.PublicFormat.SubjectPublicKeyInfo).hex()


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        miner_scheduled_job,
        'interval',
        seconds=10,
        max_instances=1,
        id='data_task'
    )
    scheduler.start()


def load_peers(peer_filename):
    loaded_peers = []
    with open(peer_filename, 'r', encoding='utf-8') as file:
        for line in file.readlines():
            line = line.strip()
            if line:
                loaded_peers.append(line)
    return loaded_peers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KaYakCoin Node')
    parser.add_argument('--nodename', type=str, required=False, help='Node name', default="node")
    parser.add_argument('--mode', type=str, required=False, help='Mode of operation', default="INIT")
    parser.add_argument('--address', type=str, required=False, help='Address', default="127.0.0.1")
    parser.add_argument('--port', type=int, required=False, help='Port number', default=2000)
    parser.add_argument('--peer', type=str, required=False, help='Peer address')

    args = parser.parse_args()
    init_state(args)

    logging.info(f"Starting node on address {args.address}:{args.port} with mode: {args.mode}")

    if args.mode == "JOIN":
        logging.info("Joining network")
        peers = load_peers(args.peer)
        init_handshake(peers)
        blockchain = get_blockchain(peers[0])
        nodeState.load_blockchain(blockchain)

    else:
        logging.info("Initializing network, creating genesis block")
        nodeState.create_genesis_block()

        logging.info("Starting miner")
        start_scheduler()

    flask_app.run(host=args.address, port=args.port, ssl_context='adhoc', use_reloader=False)
