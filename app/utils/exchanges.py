import os
import json
import requests
import pandas as pd
import websocket

# Unset proxy environment variables
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)

top_crypto_symbols = []
top_stablecoin_symbols = []
general_df = pd.DataFrame(columns=["exchange", "token", "price"])
stable_df = pd.DataFrame(columns=["exchange", "token", "price"])


def get_top_symbols():
    response = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
        },
    )
    top_crypto_symbols = [coin["symbol"].upper() for coin in response.json()]

    response = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            "vs_currency": "usd",
            "category": "stablecoins",
            "order": "market_cap_desc",
            "per_page": 25,
            "page": 1,
        },
    )
    top_stablecoin_symbols = [coin["symbol"].upper() for coin in response.json()]

    return top_crypto_symbols, top_stablecoin_symbols


def on_message(self, ws, message):
    data = json.loads(message)
    # Extract price information based on the exchange's message format
    # This is a placeholder and should be adapted to each exchange's message format
    exchange = ws.url
    token = data.get("s", "")
    price = data.get("p", 0)

    if token in top_crypto_symbols:
       general_df.loc[len(general_df)] = [exchange, token, price]
    elif token in top_stablecoin_symbols:
       stable_df.loc[len(stable_df)] = [exchange, token, price]


def on_error(ws, error):
    print(f"WebSocket error: {error}")


def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket connection closed: {close_status_code} - {close_msg}")


def on_open(ws):
    print("WebSocket connection opened")
    # Subscribe to the ticker stream for multiple tokens
    tokens = top_crypto_symbols + top_stablecoin_symbols
    params = [f"{token.lower()}@ticker" for token in tokens]
    subscribe_message = {"method": "SUBSCRIBE", "params": params, "id": 1}
    ws.send(json.dumps(subscribe_message))


def on_ping(ws, message):
    print(f"Received ping: {message}")
    ws.send(message, websocket.ABNF.OPCODE_PONG)
    print(f"Sent pong: {message}")


def run():
    global top_crypto_symbols, top_stablecoin_symbols
    top_crypto_symbols, top_stablecoin_symbols = get_top_symbols()
    endpoints = [
        "wss://ws-feed.pro.coinbase.com",  # Corrected Coinbase URL
        "wss://ws.kraken.com",
        "wss://stream.binance.com:9443/ws/!ticker@arr",  # Corrected Binance URL
        "wss://stream.crypto.com/v2/market",  # Corrected Crypto.com URL
        "wss://stream.bybit.com/realtime_public",  # Corrected Bybit URL
        "wss://ws-api.kucoin.com/endpoint",  # Corrected KuCoin URL
    ]

    websocket.enableTrace(True)
    for endpoint in endpoints:
        ws = websocket.WebSocketApp(
            endpoint,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
            on_ping=on_ping,
        )
        ws.run_forever()


if __name__ == "__main__":
    run()
