from flask import Flask, render_template, jsonify
import asyncio
import json
import websockets  # Import the websockets library

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"  # Change this in production!

WEBSOCKET_URI = "ws://localhost:8765"  # WebSocket server address


async def fetch_data_from_websocket(message):
    try:
        async with websockets.connect(WEBSOCKET_URI) as websocket:
            await websocket.send(json.dumps(message))
            data = await websocket.recv()
            return json.loads(data)
    except Exception as e:
        print(f"Error connecting to WebSocket: {e}")
        return {"error": str(e)}


def run_async_task(coroutine):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)


@app.route("/")
def index():
    return render_template("index.html")  # Assuming you have an index.html


@app.route("/api/crypto")
def get_crypto_data():
    crypto_data = run_async_task(fetch_data_from_websocket({"type": "crypto"}))
    return jsonify(crypto_data)


@app.route("/api/stablecoin")
def get_stablecoin_data():
    stablecoin_data = run_async_task(fetch_data_from_websocket({"type": "stablecoin"}))
    return jsonify(stablecoin_data)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
