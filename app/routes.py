from flask import Blueprint, jsonify, render_template
from app.utils.websocket_manager import websocket_manager

# Create a Blueprint for routes
routes = Blueprint("routes", __name__)


@routes.route("/")
def index():
    return render_template("index.html")


@routes.route("/api/prices/stablecoins", methods=["GET"])
def get_stablecoin_prices():
    stablecoin_prices = websocket_manager.get_stablecoin_prices()
    return jsonify(stablecoin_prices)


@routes.route("/api/prices/cryptocurrencies", methods=["GET"])
def get_crypto_prices():
    crypto_prices = websocket_manager.get_crypto_prices()
    return jsonify(crypto_prices)
