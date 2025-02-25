import os
import json
import requests
import pandas as pd
import websocket
import asyncio
import threading

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
    global top_crypto_symbols
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
    global top_stablecoin_symbols
    top_stablecoin_symbols = [coin["symbol"].upper() for coin in response.json()]

    return top_crypto_symbols, top_stablecoin_symbols


def get_available_trading_pairs():
    try:
        url = "https://api.binance.com/api/v3/exchangeInfo"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        trading_pairs = []
        for symbol in response.json()["symbols"]:
            base_asset = symbol["baseAsset"]
            print(f"BaseAsset: {symbol}")
            quote_asset = symbol["quoteAsset"]
            trading_pairs.append(f"{base_asset}{quote_asset}")

        return trading_pairs
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch trading pairs from Binance: {e}")
        return []


# Select the best trading pair based on preferred quote assets
def select_best_trading_pair(symbol, trading_pairs):
    preferred_pairs = ["USDT", "BUSD", "BTC", "ETH", "USDC"]

    # First, try to find a trading pair that matches the preferred pairs
    for pair in preferred_pairs:
        for trading_pair in trading_pairs:
            if trading_pair.startswith(symbol) and trading_pair.endswith(pair):
                return trading_pair

    # If no preferred pair is found, return the first trading pair that starts with the symbol
    for trading_pair in trading_pairs:
        if trading_pair.startswith(symbol):
            return trading_pair
    for trading_pair in trading_pairs:
        if trading_pair.endswith(symbol):
            return trading_pair
    for trading_pair in trading_pairs:
        if trading_pair.find(symbol) != -1:
            return trading_pair

    return None  # No suitable trading pair found


# Main function to get trading pairs for top tokens
def get_trading_pairs_for_top_tokens():
    # Get top 50 cryptos and top 25 stablecoins
    global top_crypto_symbols, top_stablecoin_symbols
    all_symbols = top_crypto_symbols + top_stablecoin_symbols

    # Get trading pairs for each symbol
    trading_pairs = {}
    pairs = get_available_trading_pairs()
    print(f"Available trading pairs: {pairs}")
    for symbol in all_symbols:
        best_pair = select_best_trading_pair(symbol, pairs)
        print(f"Best pair for symbol - {symbol}: {best_pair}")
        if best_pair:
            trading_pairs[symbol] = best_pair
        else:
            print(f"No suitable trading pair found for {symbol}")

    return trading_pairs


def on_message(ws, message):
    data = json.loads(message)
    print(f"Reveived data: {ws.url}, {data}")

    process_message(ws, data)


def process_message(ws, data):
    """
    Process a single message and update the DataFrame.
    """
    exchange = get_exchange_name(ws.url)  # Get the exchange name from the WebSocket URL
    token = ""
    price = 0.0
    if exchange == "Binance":
        token = data.get("s", "")  # Get token symbol
        price = data.get("c", 0)  # Get token price
    elif exchange == "Coinbase":
        token = data.get("product_id", "")  # Get token symbol
        price = float(data.get("price", 0))  # Get token price
    elif exchange == "Kraken":
        if isinstance(data, list) and len(data) > 3:
            token = data[-1]  # Get the pair name (e.g., "XBT/USD")
            price_info = data[1]  # Get the dictionary containing price information
            if isinstance(price_info, dict) and "c" in price_info:
                price = float(price_info["c"][0])  # Get the latest price
    elif exchange == "Gemini":
        token = data.get("symbol", "")
        price = data.get("price", 0)
    elif exchange == "Bitstamp":
        token = data.get("channel").split("_")[2]
        price = price = data.get("data", {}).get("price", 0)
        print(f"Token: {token}, Price: {price}")

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
    elif "bitstamp" in url:
        return "Bitstamp"
    elif "gemini" in url:
        return "Gemini"
    else:
        return "Unknown"


def update_price(exchange, token, price):
    global general_df, stable_df
    global top_crypto_symbols, top_stablecoin_symbols

    # Extract the base token symbol from the trading pair symbol
    # Example: "BTCUSDT" -> "BTC", "ETHBUSD" -> "ETH"
    if exchange == "Kraken" and token.startswith("XBT"):
        base_token = "BTC"
    else:
        base_token = None
        for symbol in top_crypto_symbols + top_stablecoin_symbols:
            if token.startswith(symbol) | token.startswith(symbol.lower()):
                base_token = symbol
                break

    if not base_token:
        print(f"Invalid token: {token}")
        return
    cleaned_token = token.replace("//", "")
    # Check if the base token is in top_crypto_symbols or top_stablecoin_symbols
    if base_token in top_crypto_symbols:
        mask = (general_df["exchange"] == exchange) & (
            general_df["token"] == base_token
        )
        if mask.any():
            # Update the existing row
            general_df.loc[mask, "price"] = str(price) + cleaned_token.replace(
                base_token, ""
            )
        else:
            # Add a new row
            new_row = {
                "exchange": exchange,
                "token": base_token,
                "price": str(price) + cleaned_token.replace(base_token, ""),
            }
            general_df = pd.concat(
                [general_df, pd.DataFrame([new_row])], ignore_index=True
            )

        # Sort the DataFrame according to top_crypto_symbols
        general_df["token"] = pd.Categorical(
            general_df["token"], categories=top_crypto_symbols, ordered=True
        )
        general_df.sort_values("token", inplace=True)

    elif base_token in top_stablecoin_symbols:
        mask = (stable_df["exchange"] == exchange) & (stable_df["token"] == base_token)
        if mask.any():
            # Update the existing row
            stable_df.loc[mask, "price"] = str(price) + cleaned_token.replace(
                base_token, ""
            )
        else:
            # Add a new row
            new_row = {
                "exchange": exchange,
                "token": base_token,
                "price": str(price) + cleaned_token.replace(base_token, ""),
            }
            stable_df = pd.concat(
                [stable_df, pd.DataFrame([new_row])], ignore_index=True
            )

        # Sort the DataFrame according to top_stablecoin_symbols
        stable_df["token"] = pd.Categorical(
            stable_df["token"], categories=top_stablecoin_symbols, ordered=True
        )
        stable_df.sort_values("token", inplace=True)
    else:
        print(f"Token {token} not in crypto or stablecoin lists")


def on_error(ws, error):
    print(f"WebSocket error: {error}")


def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket connection closed: {close_status_code} - {close_msg}")


def on_binance_open(ws):
    print("WebSocket connection opened")
    # Subscribe to the ticker stream for multiple tokens
    tokens = get_trading_pairs_for_top_tokens()
    print(f"Stable coin list = {tokens}")
    params = [f"{token.lower()}@ticker" for token in tokens.values()]
    subscribe_message = {"method": "SUBSCRIBE", "params": params, "id": 1}
    print(f"params: {json.dumps(subscribe_message)}")
    ws.send(json.dumps(subscribe_message))


def on_coinbase_open(ws):
    global top_crypto_symbols, top_stablecoin_symbols
    print("WebSocket connection opened")
    print(f"top tokens for coinbase = {top_crypto_symbols + top_stablecoin_symbols}")
    tokens = top_crypto_symbols + top_stablecoin_symbols
    params = [f"{token}-USD" for token in tokens]
    subscribe_message = {
        "type": "subscribe",
        "product_ids": params,
        "channels": ["ticker"],
    }
    print(f"params: {json.dumps(subscribe_message)}")
    ws.send(json.dumps(subscribe_message))


def on_kraken_open(ws):
    global top_crypto_symbols, top_stablecoin_symbols
    print("WebSocket connection opened")
    print(f"top tokens for kraken = {top_crypto_symbols + top_stablecoin_symbols}")
    tokens = top_crypto_symbols + top_stablecoin_symbols
    params = [f"{token}/USD" for token in tokens]
    subscribe_message = {
        "event": "subscribe",
        "pair": params,
        "subscription": {"name": "ticker"},
    }
    print(f"params: {json.dumps(subscribe_message)}")
    ws.send(json.dumps(subscribe_message))


def on_bitstamp_open(ws):
    global top_crypto_symbols, top_stablecoin_symbols
    print("WebSocket connection opened")
    print(f"top tokens for bitstamp = {top_crypto_symbols + top_stablecoin_symbols}")
    tokens = top_crypto_symbols + top_stablecoin_symbols
    subscribe_messages = [
        {
            "event": "bts:subscribe",
            "data": {"channel": f"live_trades_{token.lower()}usd"},
        }
        for token in tokens
    ]
    print(f"params: {json.dumps(subscribe_messages)}")
    for subscribe_message in subscribe_messages:
        ws.send(json.dumps(subscribe_message))


def on_gemini_open(ws):
    global top_crypto_symbols, top_stablecoin_symbols
    print("WebSocket connection opened")
    print(f"top tokens for gemini = {top_crypto_symbols + top_stablecoin_symbols}")
    tokens = top_crypto_symbols + top_stablecoin_symbols
    subscribe_message = {
        "type": "subscribe",
        "subscriptions": [
            {"name": "ticker", "symbols": [f"{token}USD" for token in tokens]}
        ],
    }
    print(f"params: {json.dumps(subscribe_message)}")
    ws.send(json.dumps(subscribe_message))


def on_ping(ws, message):
    print(f"Received ping: {message}")
    ws.send(message, websocket.ABNF.OPCODE_PONG)
    print(f"Sent pong: {message}")


def retrieve_general_token_info():
    return general_df.to_json(orient="records")


def retrieve_stable_token_info():
    return stable_df.to_json(orient="records")


def run_websocket(endpoint, on_open):
    ws = websocket.WebSocketApp(
        endpoint,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
        on_ping=on_ping,
    )
    ws.run_forever()


async def start_websockets():
    global top_crypto_symbols, top_stablecoin_symbols
    top_crypto_symbols, top_stablecoin_symbols = get_top_symbols()
    endpoints = [
        "wss://stream.binance.com:9443/ws",
        "wss://ws-feed.exchange.coinbase.com",
        "wss://ws.kraken.com",
        "wss://ws.bitstamp.net",
        "wss://api.gemini.com/v2/marketdata",
        # Add other endpoints here
    ]

    for endpoint in endpoints:
        if endpoint == "wss://stream.binance.com:9443/ws":
            on_open = on_binance_open
        elif endpoint == "wss://ws-feed.exchange.coinbase.com":
            on_open = on_coinbase_open
        elif endpoint == "wss://ws.kraken.com":
            on_open = on_kraken_open
        elif endpoint == "wss://ws.bitstamp.net":
            on_open = on_bitstamp_open
        elif endpoint == "wss://api.gemini.com/v2/marketdata":
            on_open = on_gemini_open
        else:
            continue

        thread = threading.Thread(target=run_websocket, args=(endpoint, on_open))
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    asyncio.run(start_websockets())
