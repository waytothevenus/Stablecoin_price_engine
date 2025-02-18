from flask import Flask
from flask_socketio import SocketIO


def create_app():
    app = Flask(__name__)
    app.config.from_object("config")

    socketio = SocketIO(app)

    # Import and register the routes blueprint
    from .routes import routes as routes_blueprint

    app.register_blueprint(routes_blueprint)

    return app, socketio


app, socketio = create_app()
