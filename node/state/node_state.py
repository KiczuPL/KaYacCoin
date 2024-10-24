import logging


class NodeState:

    def __init__(self):
        self.mode = "INIT"
        self.node_uuid = None
        self.start_peers = []
        self.connected_peers = []
        self.blockchain = []
        self.private_key = None
        self.node_id = None
        self.node_address = None
        self.node_port = None
        self.mempool = []
        self.verify_ssl_cert = False

    def add_peer(self, peer):
        if peer in self.connected_peers:
            logging.info(f"Peer {peer} already connected")
            return
        self.connected_peers.append(peer)
        logging.info(f"Added peer: {peer}, connected peers: {len(self.connected_peers)}")

    def remove_peer(self, peer):
        if peer not in self.connected_peers:
            logging.info(f"Peer {peer} not connected")
            return
        self.connected_peers.remove(peer)
        logging.info(f"Removed peer: {peer}, connected peers: {len(self.connected_peers)}")

    def get_callback_address(self):
        return f"{self.node_address}:{self.node_port}"

    def print_mempool(self):
        logging.info(f"MemPool: {self.mempool}")


nodeState = NodeState()
