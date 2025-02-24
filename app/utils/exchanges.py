import os
import json
import requests
import pandas as pd
import websocket
import asyncio

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
    top_crypto_symbols = [coin["symbol"].upper() + "USDT" for coin in response.json()]

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
    top_stablecoin_symbols = [
        coin["symbol"].upper() + "USDT" for coin in response.json()
    ]

    return top_crypto_symbols, top_stablecoin_symbols


def on_message(ws, message):
    data = json.loads(message)
    if isinstance(data, list):
        for item in data:
            process_message(ws, item)
    else:
        process_message(ws, data)


def process_message(ws, data):
    """
    Process a single message and update the DataFrame.
    """
    exchange = get_exchange_name(ws.url)  # Get the exchange name from the WebSocket URL
    token = data.get("s", "")  # Get token symbol
    price = data.get("c", 0)  # Get token price

    # Validate token and price
    if not token or not price:
        print(f"Invalid data: {data}")
        return

    # Update the DataFrame
    update_price(exchange, token, float(price))


def get_exchange_name(url):
    """
    Extract the exchange name from the WebSocket URL.
    """
    if "binance" in url:
        return "Binance"
    elif "coinbase" in url:
        return "Coinbase"
    elif "kraken" in url:
        return "Kraken"
    elif "crypto.com" in url:
        return "Crypto.com"
    elif "bybit" in url:
        return "Bybit"
    elif "kucoin" in url:
        return "KuCoin"
    else:
        return "Unknown"


def update_price(exchange, token, price):
    global general_df, stable_df

    # Check if the token and exchange already exist in the DataFrame
    if token in top_crypto_symbols:
        mask = (general_df["exchange"] == exchange) & (general_df["token"] == token)
        if mask.any():
            # Update the existing row
            general_df.loc[mask, "price"] = price
        else:
            # Add a new row
            new_row = {"exchange": exchange, "token": token, "price": price}
            general_df = pd.concat(
                [general_df, pd.DataFrame([new_row])], ignore_index=True
            )

        # Sort the DataFrame according to top_crypto_symbols
        general_df["token"] = pd.Categorical(
            general_df["token"], categories=top_crypto_symbols, ordered=True
        )
        general_df.sort_values("token", inplace=True)

    elif token in top_stablecoin_symbols:
        mask = (stable_df["exchange"] == exchange) & (stable_df["token"] == token)
        if mask.any():
            # Update the existing row
            stable_df.loc[mask, "price"] = price
        else:
            # Add a new row
            new_row = {"exchange": exchange, "token": token, "price": price}
            stable_df = pd.concat(
                [stable_df, pd.DataFrame([new_row])], ignore_index=True
            )

        # Sort the DataFrame according to top_stablecoin_symbols
        # stable_df["token"] = pd.Categorical(
        #     stable_df["token"], categories=top_stablecoin_symbols, ordered=True
        # )
        # stable_df.sort_values("token", inplace=True)


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


def retrieve_general_token_info():
    return general_df.to_json(orient="records")


def retrieve_stable_token_info():
    return stable_df.to_json(orient="records")


async def run():
    import time

    # time.sleep(10)
    global top_crypto_symbols, top_stablecoin_symbols
    top_crypto_symbols, top_stablecoin_symbols = get_top_symbols()
    endpoints = [
        "wss://stream.binance.com:9443/ws/!ticker@arr",  # Corrected Binance URL
    ]

    websocket.enableTrace(False)
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
    asyncio.run(run())
