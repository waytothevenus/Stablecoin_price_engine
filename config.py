class Config:
    SECRET_KEY = 'your_secret_key_here'
    WS_AUTH_TOKEN = 'your_auth_token_here'
    EXCHANGE_API_KEYS = {
        'exchange1': 'api_key_1',
        'exchange2': 'api_key_2',
        'exchange3': 'api_key_3',
        'exchange4': 'api_key_4',
        'exchange5': 'api_key_5',
    }
    WS_URLS = {
        'exchange1': 'wss://exchange1.websocket.url',
        'exchange2': 'wss://exchange2.websocket.url',
        'exchange3': 'wss://exchange3.websocket.url',
        'exchange4': 'wss://exchange4.websocket.url',
        'exchange5': 'wss://exchange5.websocket.url',
    }
    TOP_CRYPTO_COUNT = 50
    TOP_STABLECOIN_COUNT = 25