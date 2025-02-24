import asyncio
import websockets
import json
from config import Config
from app.utils.exchanges import retrieve_general_token_info, retrieve_stable_token_info


class WebSocketManager:
    def __init__(self):
        self.connected_clients = set()

    async def handler(self, websocket, path):
        # Authenticate client
        token = websocket.request_headers.get("Authorization")
        if token != Config.WS_AUTH_TOKEN:
            await websocket.close()
            return

        self.connected_clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data["type"] == "crypto":
                        # Fetch and send crypto data
                        crypto_data = retrieve_general_token_info()
                        await websocket.send(json.dumps(crypto_data))
                    elif data["type"] == "stablecoin":
                        # Fetch and send stablecoin data
                        stablecoin_data = retrieve_stable_token_info()
                        await websocket.send(json.dumps(stablecoin_data))
                    else:
                        await websocket.send(
                            json.dumps({"error": "Invalid message type"})
                        )
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Invalid JSON"}))
                except KeyError:
                    await websocket.send(json.dumps({"error": "Missing 'type' field"}))
                except Exception as e:
                    await websocket.send(json.dumps({"error": str(e)}))
        except Exception as e:
            print(f"Error in handler: {e}")
        finally:
            self.connected_clients.remove(websocket)

    async def start_server(self):
        print("WebSocket server starting")
        async with websockets.serve(self.handler, "0.0.0.0", 8765):
            await asyncio.Future()  # Run forever


websocket_manager = WebSocketManager()


async def start_websocket_server():
    await websocket_manager.start_server()


if __name__ == "__main__":
    asyncio.run(start_websocket_server())
