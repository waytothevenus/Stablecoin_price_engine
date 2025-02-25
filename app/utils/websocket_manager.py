import asyncio
import websockets
import json
from config import Config
from app.utils.exchanges import retrieve_general_token_info, retrieve_stable_token_info


class WebSocketManager:
    def __init__(self):
        self.connected_clients = set()

    async def handler(self, websocket):

        self.connected_clients.add(websocket)
        print(f"New client connected: {websocket.remote_address}")
        try:
            async for message in websocket:
                try:
                    print(f"Received message: {message}")
                    data = json.loads(message)
                    if "type" not in data:
                        await websocket.send(
                            json.dumps({"error": "Missing 'type' field"})
                        )
                        continue

                    if data["type"] == "crypto":
                        # Fetch and send crypto data
                        try:
                            crypto_data = retrieve_general_token_info()
                            await websocket.send(crypto_data)
                        except Exception as e:
                            print(f"Error fetching crypto data: {e}")
                            await websocket.send(
                                json.dumps({"error": "Failed to fetch crypto data"})
                            )
                    elif data["type"] == "stablecoin":
                        # Fetch and send stablecoin data
                        try:
                            stablecoin_data = retrieve_stable_token_info()
                            await websocket.send(stablecoin_data)
                        except Exception as e:
                            print(f"Error fetching stablecoin data: {e}")
                            await websocket.send(
                                json.dumps({"error": "Failed to fetch stablecoin data"})
                            )
                    else:
                        await websocket.send(
                            json.dumps({"error": "Invalid message type"})
                        )
                except json.JSONDecodeError:
                    print("Invalid JSON received")
                    await websocket.send(json.dumps({"error": "Invalid JSON"}))
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    await websocket.send(json.dumps({"error": "Internal server error"}))
        except websockets.ConnectionClosed:
            print(f"Client disconnected: {websocket.remote_address}")
        except Exception as e:
            print(f"Error in handler: {e}")
        finally:
            self.connected_clients.remove(websocket)
            print(f"Client removed: {websocket.remote_address}")

    async def start_server(self):
        print("WebSocket server starting on ws://0.0.0.0:8765")
        async with websockets.serve(self.handler, "0.0.0.0", 8765):
            await asyncio.Future()  # Run forever


websocket_manager = WebSocketManager()


async def start_websocket_server():
    await websocket_manager.start_server()


if __name__ == "__main__":
    asyncio.run(start_websocket_server())
