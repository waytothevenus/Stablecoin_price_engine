const cryptoPricesTable = document.getElementById("crypto-prices");
const stablecoinPricesTable = document.getElementById("stablecoin-prices");

const ws = new WebSocket("ws://localhost:8765");

ws.onopen = function () {
  console.log("WebSocket connection opened");
};

ws.onmessage = function (event) {
  const data = JSON.parse(event.data);
  updatePrices(data);
};

ws.onclose = function () {
  console.log("WebSocket connection closed");
};

function updatePrices(data) {
  const { exchange, token, price } = data;

  if (top_crypto_symbols.includes(token)) {
    updateTable(cryptoPricesTable, exchange, token, price);
  } else if (top_stablecoin_symbols.includes(token)) {
    updateTable(stablecoinPricesTable, exchange, token, price);
  }
}

function updateTable(table, exchange, token, price) {
  let row = document.getElementById(token);
  if (!row) {
    row = document.createElement("tr");
    row.id = token;
    row.innerHTML = `
            <td>${token}</td>
            <td id="${token}-Binance"></td>
            <td id="${token}-Coinbase"></td>
            <td id="${token}-Kraken"></td>
            <td id="${token}-Bitstamp"></td>
            <td id="${token}-Gemini"></td>
        `;
    table.appendChild(row);
  }
  document.getElementById(`${token}-${exchange}`).innerText = price;
}
