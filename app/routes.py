from flask import Blueprint, jsonify
from app.utils.websocket_manager import websocket_manager

# Create a Blueprint for routes
routes = Blueprint("routes", __name__)


@routes.route("/")
def index():
    return "Welcome to the Crypto Server!"


@routes.route("/api/prices/stablecoins", methods=["GET"])
def get_stablecoin_prices():
    stablecoin_prices = websocket_manager.get_stablecoin_prices()
    return jsonify(stablecoin_prices)


@routes.route("/api/prices/cryptocurrencies", methods=["GET"])
def get_crypto_prices():
    crypto_prices = websocket_manager.get_crypto_prices()
    return jsonify(crypto_prices)
