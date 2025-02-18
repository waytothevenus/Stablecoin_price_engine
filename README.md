# Flask Crypto Server

This project is a Flask-based web application that connects to multiple cryptocurrency exchanges via secure WebSockets to retrieve real-time price data for cryptocurrencies and stablecoins. It provides an aggregate feed of prices and displays them in a user-friendly web interface.

## Features

- Connects to at least five major cryptocurrency exchanges.
- Retrieves prices for the top 50 cryptocurrencies and the top 25 stablecoins.
- Updates prices in two separate pandas DataFrames held in memory.
- Allows WebSocket clients to connect and retrieve an aggregate feed for either stablecoins or cryptocurrency prices with authorization.
- Real-time price updates displayed using a simple web app built with Bootstrap, HTML, and JavaScript.

## Project Structure

```
flask-crypto-server
├── app
│   ├── __init__.py          # Initializes the Flask application and sets up configurations
│   ├── main.py              # Entry point for the application
│   ├── routes.py            # Defines routes for the web application
│   ├── static
│   │   ├── css
│   │   │   └── styles.css   # CSS styles for the web application
│   │   └── js
│   │       └── scripts.js    # JavaScript code for handling WebSocket connections
│   ├── templates
│   │   └── index.html       # Main HTML template for the web application
│   └── utils
│       ├── exchanges.py     # Functions to connect to exchanges and retrieve price data
│       └── websocket_manager.py # Manages WebSocket connections and client interactions
├── requirements.txt          # Lists project dependencies
├── config.py                 # Configuration settings for the application
└── README.md                 # Documentation for the project
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd flask-crypto-server
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the application by editing `config.py` with your WebSocket authentication details and API keys.

## Usage

1. Run the application:
   ```
   python app/main.py
   ```

2. Open your web browser and navigate to `http://localhost:5000` to view the application.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.