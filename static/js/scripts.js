const cryptoPricesTable = document.getElementById("crypto-prices");
const stablecoinPricesTable = document.getElementById("stablecoin-prices");

let authToken = null; // Store the authentication token
let ws = null; // Store the WebSocket instance
let dataInterval; // Store the interval ID

function connectWebSocket() {
  ws = new WebSocket("ws://localhost:8765");

  ws.onopen = function () {
    console.log("WebSocket connection opened");
  };

  ws.onmessage = function (event) {
    const data = JSON.parse(event.data);

    if (data.token) {
      // Received the authentication token from the server
      authToken = data.token;
      console.log("Received authentication token:", authToken);

      // Now that we have the token, send it back to authenticate
      ws.send(JSON.stringify({ token: authToken }));

      // After sending the token, request initial data every 1 second
      dataInterval = setInterval(requestData, 1000);
    } else if (data.error) {
      // Handle errors from the server (e.g., authentication failure)
      console.error("WebSocket error:", data.error);
      clearInterval(dataInterval); // Clear the interval on error
      ws.close(); // Close the connection if there's an error
    } else if (data.prices) {
      // Process price data
      updatePrices(data.type, JSON.parse(data.prices));
    } else {
      console.log("Received data:", data);
    }
  };

  ws.onclose = function () {
    console.log("WebSocket connection closed");
    clearInterval(dataInterval); // Clear the interval on close
    // Attempt to reconnect after a delay (e.g., 5 seconds)
    setTimeout(connectWebSocket, 5000);
  };

  ws.onerror = function (error) {
    console.error("WebSocket error:", error);
    clearInterval(dataInterval); // Clear the interval on error
  };
}

function requestData() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "crypto" }));
    ws.send(JSON.stringify({ type: "stablecoin" }));
  } else {
    console.log("WebSocket is not open.  Attempting to reconnect.");
    clearInterval(dataInterval); // Stop the interval if WebSocket is not open
    connectWebSocket(); // Reconnect
  }
}

function updatePrices(type, prices) {
  prices.forEach(({ exchange, token, price }) => {
    if (type === "crypto") {
      updateTable(cryptoPricesTable, exchange, token, price);
    }

    if (type === "stablecoin") {
      updateTable(stablecoinPricesTable, exchange, token, price);
    }
  });
}

function updateTable(table, exchange, token, price) {
  let rowId = token;
  let row = document.getElementById(rowId);

  if (!row) {
    row = document.createElement("tr");
    row.id = rowId;
    row.innerHTML = `
            <td>${token}</td>
            <td id="${rowId}-Binance">-</td>
            <td id="${rowId}-Coinbase">-</td>
            <td id="${rowId}-Kraken">-</td>
            <td id="${rowId}-Bitstamp">-</td>
            <td id="${rowId}-Gemini">-</td>
        `;
    table.appendChild(row);
  }

  const priceCellId = `${rowId}-${exchange}`;
  const priceCell = document.getElementById(priceCellId);

  if (priceCell) {
    console.log("Price update: ", priceCellId, price);
    priceCell.innerText = price;
  } else {
    console.warn(`Cell with id ${priceCellId} not found`);
  }
}

// Initiate the WebSocket connection
connectWebSocket();
