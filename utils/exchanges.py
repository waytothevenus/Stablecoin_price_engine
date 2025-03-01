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


exchanges = ["Binance", "Kraken", "Coinbase", "Bitstamp", "Gemini"]


def get_top_symbols():
    # Get top cryptocurrencies
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
    # prices = [coin["current_price"] for coin in response.json()]

    # Create records for general_df
    for token in top_crypto_symbols:
        for exchange in exchanges:
            general_df.loc[len(general_df)] = [exchange, token, ""]

    # Get top stablecoins
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
    # stable_prices = [coin["current_price"] for coin in response.json()]
    # Create records for stable_df
    for token in top_stablecoin_symbols:
        for exchange in exchanges:
            stable_df.loc[len(stable_df)] = [exchange, token, ""]

    return top_crypto_symbols, top_stablecoin_symbols


async def update_top_symbols_periodically():
    global top_crypto_symbols, top_stablecoin_symbols
    while True:
        top_crypto_symbols, top_stablecoin_symbols = get_top_symbols()
        print(f"Updated top symbols: {top_crypto_symbols + top_stablecoin_symbols}")
        await asyncio.sleep(60)  # Wait for 1 minute


def get_available_trading_pairs(exchange):
    match exchange:
        case "Binance":
            try:
                url = "https://api.binance.com/api/v3/exchangeInfo"
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for HTTP errors
                trading_pairs = []
                for symbol in response.json()["symbols"]:
                    base_asset = symbol["baseAsset"]
                    quote_asset = symbol["quoteAsset"]
                    trading_pairs.append(f"{base_asset}{quote_asset}")
                print(f"Trading pairs: {trading_pairs}")

                return trading_pairs
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch trading pairs from Binance: {e}")
                return []
        case "Coinbase":
            try:
                url = "https://api.exchange.coinbase.com/products"
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for HTTP errors
                trading_pairs = []
                for product in response.json():
                    base_asset = product["base_currency"]
                    quote_asset = product["quote_currency"]
                    trading_pairs.append(f"{base_asset}-{quote_asset}")
                return trading_pairs
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch trading pairs from Coinbase: {e}")
                return []

        case "Kraken":
            try:
                url = "https://api.kraken.com/0/public/AssetPairs"
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for HTTP errors
                trading_pairs = []
                for pair, details in response.json()["result"].items():
                    base = details.get("base")
                    quote = details.get("quote")
                    if quote == "ZUSD":
                        quote = "USD"
                    if base == "XXRP":
                        base = "XRP"
                    if base == "XLTC":
                        base = "LTC"
                    if base == "XXLM":
                        base = "XLM"
                    if quote == "FIUSD":
                        quote == "USDT"
                    trading_pairs.append(f"{base}/{quote}")
                trading_pairs.append("BTC/USD")
                return trading_pairs
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch trading pairs from Kraken: {e}")
                return []

        case "Bitstamp":
            try:
                url = "https://www.bitstamp.net/api/v2/trading-pairs-info/"
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for HTTP errors
                trading_pairs = []
                for pair in response.json():
                    trading_pairs.append(pair.get("url_symbol"))
                return trading_pairs
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch trading pairs from Bitstamp: {e}")
                return []
        case "Gemini":
            try:
                url = "https://api.gemini.com/v1/symbols"
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for HTTP errors
                trading_pairs = response.json()
                return trading_pairs
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch trading pairs from Gemini: {e}")
                return []
        case _:
            return []


# Select the best trading pair based on preferred quote assets
def select_best_trading_pair(symbol, trading_pairs):
    preferred_pairs = [
        "USDT",
        "USD",
        "BUSD",
        "BTC",
        "ETH",
        "USDC",
    ]

    # First, try to find a trading pair that matches the preferred pairs
    for pair in preferred_pairs:
        for trading_pair in trading_pairs:
            if (
                trading_pair.startswith(symbol)
                | trading_pair.startswith(symbol.lower())
            ) and (trading_pair.endswith(pair) | trading_pair.endswith(pair.lower())):
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
def get_trading_pairs_for_top_tokens(exchange):
    # Get top 50 cryptos and top 25 stablecoins
    global top_crypto_symbols, top_stablecoin_symbols
    all_symbols = top_crypto_symbols + top_stablecoin_symbols

    # Get trading pairs for each symbol
    trading_pairs = {}
    pairs = get_available_trading_pairs(exchange)
    print(f"Available pairs for {exchange}: {pairs}")
    for symbol in all_symbols:
        best_pair = select_best_trading_pair(symbol, pairs)
        if best_pair:
            trading_pairs[symbol] = best_pair

    return trading_pairs


def on_message(ws, message):
    data = json.loads(message)
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
        if data.get("channel") == "ticker":
            ticker_data = data.get("data", [])[0]
            token = ticker_data.get("symbol", "")
            price = ticker_data.get("last", 0)
    elif exchange == "Gemini":
        token = data.get("symbol", "")
        changes = data.get("changes", [])
        if changes and isinstance(changes[0], list) and len(changes[0]) > 1:
            price = float(changes[0][1])
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
    if exchange == "Kraken" and (token.startswith("XBT") or token.startswith("BTC")):
        base_token = "BTC"
    else:
        base_token = None
        for symbol in top_crypto_symbols + top_stablecoin_symbols:
            if token.startswith(symbol) or token.startswith(symbol.lower()):
                base_token = symbol
                break

    if not base_token:
        return
    cleaned_token = token.replace("\\", "").replace("/", "").replace("-", "")
    # Check if the base token is in top_crypto_symbols or top_stablecoin_symbols
    if base_token in top_crypto_symbols or base_token.upper() in top_crypto_symbols:
        mask = (general_df["exchange"] == exchange) & (
            general_df["token"] == base_token
        )
        if mask.any():
            # Update the existing row
            general_df.loc[mask, "price"] = str(price) + cleaned_token.replace(
                base_token, ""
            ).replace(base_token.lower(), "")
            # print(f"Token Price updated {exchange} - {base_token} - {price}")
        else:
            # Add a new row
            new_row = {
                "exchange": exchange,
                "token": base_token,
                "price": str(price)
                + cleaned_token.replace(base_token, "").replace(base_token.lower(), ""),
            }
            general_df = pd.concat(
                [general_df, pd.DataFrame([new_row])], ignore_index=True
            )
            # print(f"New token price inserted {new_row}")

        # Sort the DataFrame according to top_crypto_symbols
        general_df["token"] = pd.Categorical(
            general_df["token"], categories=top_crypto_symbols, ordered=True
        )
        general_df.sort_values("token", inplace=True)

    if (
        base_token in top_stablecoin_symbols
        or base_token.upper() in top_stablecoin_symbols
    ):
        mask = (stable_df["exchange"] == exchange) & (stable_df["token"] == base_token)
        if mask.any():
            # Update the existing row
            stable_df.loc[mask, "price"] = str(price) + cleaned_token.replace(
                base_token, ""
            ).replace(base_token.lower(), "")
            print(f"Stable Token Price updated {exchange} - {base_token} - {price}")

        else:
            # Add a new row
            new_row = {
                "exchange": exchange,
                "token": base_token,
                "price": str(price)
                + cleaned_token.replace(base_token, "").replace(base_token.lower(), ""),
            }
            stable_df = pd.concat(
                [stable_df, pd.DataFrame([new_row])], ignore_index=True
            )
            print(f"New stable token price inserted {new_row}")

        # Sort the DataFrame according to top_stablecoin_symbols
        stable_df["token"] = pd.Categorical(
            stable_df["token"], categories=top_stablecoin_symbols, ordered=True
        )
        stable_df.sort_values("token", inplace=True)


def on_error(ws, error):
    print(f"WebSocket error: {error} in {ws.url}")


def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket connection closed: {close_status_code} - {close_msg} - {ws.url}")


def on_binance_open(ws):
    print("WebSocket for Binance connection opened")
    # Subscribe to the ticker stream for multiple tokens
    pairs = get_trading_pairs_for_top_tokens("Binance")
    print(f"Pairs for Binance = {pairs}")
    params = [f"{pair.lower()}@ticker" for pair in pairs.values()]
    subscribe_message = {"method": "SUBSCRIBE", "params": params, "id": 1}
    print(f"params: {json.dumps(subscribe_message)}")
    ws.send(json.dumps(subscribe_message))


def on_coinbase_open(ws):

    print("WebSocket for Coinbase connection opened")
    # Subscribe to the ticker stream for multiple tokens
    pairs = get_trading_pairs_for_top_tokens("Coinbase")
    print(f"Pairs for Coinbase = {pairs}")
    params = [f"{pair}" for pair in pairs.values()]
    subscribe_message = {
        "type": "subscribe",
        "product_ids": params,
        "channels": ["ticker"],
    }
    print(f"params: {json.dumps(subscribe_message)}")
    ws.send(json.dumps(subscribe_message))


def on_kraken_open(ws):
    print("WebSocket for Kraken connection opened")
    # Subscribe to the ticker stream for multiple tokens
    pairs = get_trading_pairs_for_top_tokens("Kraken")
    print(f"Pairs for Kraken = {pairs}")
    params = [f"{pair}" for pair in pairs.values()]
    subscribe_message = {
        "method": "subscribe",
        "params": {"channel": "ticker", "symbol": params},
    }
    print(f"params: {json.dumps(subscribe_message)}")
    ws.send(json.dumps(subscribe_message))


def on_bitstamp_open(ws):
    print("WebSocket for Bitstamp connection opened")
    # Subscribe to the ticker stream for multiple tokens
    pairs = get_trading_pairs_for_top_tokens("Bitstamp")
    print(f"Pairs for Bitstamp = {pairs}")
    subscribe_messages = [
        {
            "event": "bts:subscribe",
            "data": {"channel": f"live_trades_{pair.lower()}"},
        }
        for pair in pairs.values()
    ]
    print(f"params: {json.dumps(subscribe_messages)}")
    for subscribe_message in subscribe_messages:
        ws.send(json.dumps(subscribe_message))


def on_gemini_open(ws):
    print("WebSocket for Gemini connection opened")
    # Subscribe to the ticker stream for multiple tokens
    pairs = get_trading_pairs_for_top_tokens("Gemini")
    print(f"Pairs for Gemini = {pairs}")
    subscribe_message = {
        "type": "subscribe",
        "subscriptions": [
            {
                "name": "l2",
                "symbols": [f"{pair}" for pair in pairs.values()],
            }
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
        "wss://ws.kraken.com/v2",
        "wss://ws.bitstamp.net",
        "wss://api.gemini.com/v2/marketdata",
        # Add other endpoints here
    ]

    for endpoint in endpoints:
        if endpoint == "wss://stream.binance.com:9443/ws":
            on_open = on_binance_open
        elif endpoint == "wss://ws-feed.exchange.coinbase.com":
            on_open = on_coinbase_open
        elif endpoint == "wss://ws.kraken.com/v2":
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


async def run():
    await asyncio.gather(update_top_symbols_periodically(), start_websockets())


if __name__ == "__main__":
    asyncio.run(run())
