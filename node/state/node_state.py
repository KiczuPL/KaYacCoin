import asyncio
import websockets
import logging
import json


class NodeState:

    def __init__(self):
        self.mode = "INIT"
        self.start_peers = []
        self.peers = []
        self.peers_websocket_connections = []
        self.blockchain = []
        self.private_key = None
        self.public_key = None
        self.node_id = None
        self.node_address = None
        self.node_port = None

    def broadcast(self, message):
        print(f"broadcasting message: {message}")
        for peer in self.peers_websocket_connections:
            asyncio.create_task(peer.send(message))

    async def message_handler(self, websocket):
        self.peers_websocket_connections.append(websocket)
        logging.info(
            f"new peer connected started: {websocket.remote_address}, current peers: {len(nodeState.peers_websocket_connections)}")
        try:
            async for message in websocket:
                data = json.loads(message)
                logging.info(f"received message: {data}")
                # await websocket.send(message)
        except websockets.ConnectionClosedError:
            logging.error(f"peer disconnected: {websocket.remote_address}")

        nodeState.peers_websocket_connections.remove(websocket)
        logging.info(
            f"peer disconnected: {websocket.remote_address}, current peers: {len(nodeState.peers_websocket_connections)}")

    async def start_socket(self):
        async with websockets.serve(self.message_handler, self.node_address, self.node_port):
            await asyncio.Future()

    async def connect_to_start_peers(self):
        for peer in self.start_peers:
            logging.info(f"connecting to peer: {peer}")
            async with websockets.connect(f"ws://{peer}") as websocket:
                self.peers_websocket_connections.append(websocket)
                logging.info(f"connected to peer: {peer}")
                await asyncio.Future()


nodeState = NodeState()
