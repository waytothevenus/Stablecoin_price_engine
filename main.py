from flask import Flask
from flask_socketio import SocketIO
import asyncio
import threading
from app.utils.exchanges import run as connect_to_exchanges
from app.utils.websocket_manager import websocket_manager, start_websocket_server
from app.routes import routes  # Import the routes blueprint


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    socketio = SocketIO(app)

    # Register the routes blueprint
    app.register_blueprint(routes)

    # Run the exchange connections and WebSocket server in a separate asyncio event loop
    def start_async_tasks():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            asyncio.gather(
                connect_to_exchanges(),  # Connect to exchanges
                start_websocket_server(),  # Start the WebSocket server
            )
        )

    # Start the async tasks in a separate thread
    thread = threading.Thread(target=start_async_tasks)
    thread.daemon = True  # Daemonize the thread to stop it when the main program exits
    thread.start()

    return app, socketio


if __name__ == "__main__":
    app, socketio = create_app()
    socketio.run(app, host="0.0.0.0", port=5000)
