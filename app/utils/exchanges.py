import pandas as pd
import json
import asyncio
import websockets
import requests


class ExchangeClient:
    def __init__(self, url, top_crypto_symbols, top_stablecoin_symbols):
        self.url = url
        self.crypto_data = pd.DataFrame(columns=["symbol", "price", "exchange"])
        self.stablecoin_data = pd.DataFrame(columns=["symbol", "price", "exchange"])
        self.top_crypto_symbols = top_crypto_symbols
        self.top_stablecoin_symbols = top_stablecoin_symbols

    async def connect(self):
        async with websockets.connect(self.url) as websocket:
            while True:
                response = await websocket.recv()
                self.update_data(response)

    def update_data(self, response):
        data = json.loads(response)
        for item in data:
            symbol = item["symbol"]
            price = item["price"]
            exchange = self.url.split(".")[1]  
            if symbol in self.top_crypto_symbols:
                self.crypto_data = self.crypto_data.append(
                    {"symbol": symbol, "price": price, "exchange": exchange},
                    ignore_index=True,
                )
            elif symbol in self.top_stablecoin_symbols:
                self.stablecoin_data = self.stablecoin_data.append(
                    {"symbol": symbol, "price": price, "exchange": exchange},
                    ignore_index=True,
                )


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
    top_crypto_symbols = [coin["symbol"] for coin in response.json()]

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
    top_stablecoin_symbols = [coin["symbol"] for coin in response.json()]

    return top_crypto_symbols, top_stablecoin_symbols


async def main():
    top_crypto_symbols, top_stablecoin_symbols = get_top_symbols()
    exchanges = [
        "wss://ws-feed.pro.coinbase.com",
        "wss://ws.kraken.com",
        "wss://stream.binance.com:9443/ws",
        "wss://stream.crypto.com/v2/market",
        "wss://stream.bybit.com/realtime",
        "wss://api.kucoin.com/api/v1/bullet-public",
    ]

    clients = [
        ExchangeClient(url, top_crypto_symbols, top_stablecoin_symbols)
        for url in exchanges
    ]
    await asyncio.gather(*[client.connect() for client in clients])


if __name__ == "__main__":
    asyncio.run(main())
