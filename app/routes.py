from flask import Blueprint, jsonify, render_template
import app.utils.exchanges as exchanges

# Create a Blueprint for routes
routes = Blueprint("routes", __name__)


@routes.route("/")
def index():
    return render_template("index.html")


@routes.route("/api/prices/stablecoins", methods=["GET"])
def get_stablecoin_prices():
    stablecoin_prices = exchanges.retrieve_stable_token_info()
    return jsonify(stablecoin_prices)


@routes.route("/api/prices/cryptocurrencies", methods=["GET"])
def get_crypto_prices():
    crypto_prices = exchanges.retrieve_general_token_info()
    return jsonify(crypto_prices)
