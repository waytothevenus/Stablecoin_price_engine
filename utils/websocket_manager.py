import asyncio
import websockets
import json
import secrets  # For generating secure tokens
from exchanges import retrieve_general_token_info, retrieve_stable_token_info
from exchanges import run as connect_to_exchanges


class WebSocketManager:
    def __init__(self):
        self.connected_clients = set()
        self.tokens = {}  # Store tokens and associated client info (e.g., IP address)
        self.valid_tokens = set()  # In-memory set of valid tokens

    def generate_token(self, client_address):
        """Generates a unique token for a client."""
        token = secrets.token_hex(16)  # 16 bytes = 32 hex characters
        self.tokens[token] = client_address  # Store client info with the token
        self.valid_tokens.add(token)  # Add token to the set of valid tokens
        return token

    def validate_token(self, token, client_address):
        """Validates a token against the client's address."""
        if token in self.valid_tokens and self.tokens.get(token) == client_address:
            return True
        return False

    def remove_token(self, token):
        """Removes a token when a client disconnects or logs out."""
        if token in self.tokens:
            del self.tokens[token]
            self.valid_tokens.discard(token)

    async def authenticate(self, websocket):
        """Authenticates the WebSocket connection using a token."""
        try:
            auth_message = await websocket.recv()
            try:
                auth_data = json.loads(auth_message)
                token = auth_data.get("token")
                if not token:
                    await websocket.send(json.dumps({"error": "Missing token"}))
                    return False
                client_address = websocket.remote_address
                if self.validate_token(token, client_address):
                    print(f"Client authenticated: {client_address} with token {token}")
                    return True
                else:
                    await websocket.send(json.dumps({"error": "Invalid token"}))
                    return False
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Invalid JSON"}))
                return False
        except asyncio.TimeoutError:
            await websocket.send(json.dumps({"error": "Authentication timeout"}))
            return False
        except Exception as e:
            print(f"Authentication error: {e}")
            await websocket.send(json.dumps({"error": "Authentication failed"}))
            return False

    async def handler(self, websocket):
        client_address = websocket.remote_address
        print(f"New client attempting to connect: {client_address}")

        # Generate and send token to the client
        token = self.generate_token(client_address)
        await websocket.send(json.dumps({"token": token}))
        print(f"Token sent to {client_address}: {token}")

        # Authenticate the client
        if not await self.authenticate(websocket):
            print(f"Authentication failed for {client_address}")
            await websocket.close(code=4001, reason="Authentication failed")
            return

        self.connected_clients.add(websocket)
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
                        try:
                            crypto_data = retrieve_general_token_info()
                            await websocket.send(
                                json.dumps({"type": "crypto", "prices": crypto_data})
                            )
                        except Exception as e:
                            print(f"Error fetching crypto data: {e}")
                            await websocket.send(
                                json.dumps({"error": "Failed to fetch crypto data"})
                            )

                    elif data["type"] == "stablecoin":
                        try:
                            stablecoin_data = retrieve_stable_token_info()
                            await websocket.send(
                                json.dumps(
                                    {"type": "stablecoin", "prices": stablecoin_data}
                                )
                            )
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
            print(f"Client disconnected: {client_address}")
        except Exception as e:
            print(f"Error in handler: {e}")
        finally:
            self.connected_clients.remove(websocket)
            self.remove_token(token)  # Remove the token on disconnect
            print(f"Client removed: {client_address}")

    async def start_server(self):
        print("WebSocket server starting on ws://0.0.0.0:8765")
        async with websockets.serve(self.handler, "0.0.0.0", 8765):
            await asyncio.Future()  # Run forever


websocket_manager = WebSocketManager()


async def start_websocket_server():
    await websocket_manager.start_server()


async def main():
    websocket_task = asyncio.create_task(start_websocket_server())
    print("Connecting to exchanges...")
    try:
        await connect_to_exchanges()
        print("Connected to exchanges.")
    except Exception as e:
        print(f"Failed to connect to exchanges: {e}")
    await websocket_task


if __name__ == "__main__":
    asyncio.run(main())
