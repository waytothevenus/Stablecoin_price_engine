import asyncio
import websockets
import json
from config import Config

connected_clients = set()
crypto_data = {}  
stablecoin_data = {} 


class WebSocketManager:
    def __init__(self):
        self.connected_clients = set()
        self.crypto_data = {}
        self.stablecoin_data = {}

    async def handler(self, websocket, path):
        token = websocket.request_headers.get("Authorization")
        if token != Config.WS_AUTH_TOKEN:
            await websocket.close()
            return

        self.connected_clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                if data["type"] == "crypto":
                    await websocket.send(json.dumps(self.crypto_data))
                elif data["type"] == "stablecoin":
                    await websocket.send(json.dumps(self.stablecoin_data))
        finally:
            self.connected_clients.remove(websocket)

    async def start_server(self):
        async with websockets.serve(self.handler, "localhost", 8765):
            await asyncio.Future()  

    def get_stablecoin_prices(self):
        return self.stablecoin_data

    def get_crypto_prices(self):
        return self.crypto_data

    def update_crypto_data(self, new_data):
        self.crypto_data = new_data
        self._broadcast({"type": "crypto", "data": self.crypto_data})

    def update_stablecoin_data(self, new_data):
        self.stablecoin_data = new_data
        self._broadcast({"type": "stablecoin", "data": self.stablecoin_data})

    def _broadcast(self, message):
        for client in self.connected_clients:
            asyncio.create_task(client.send(json.dumps(message)))


websocket_manager = WebSocketManager()


async def start_websocket_server():
    await websocket_manager.start_server()


if __name__ == "__main__":
    asyncio.run(start_websocket_server())
