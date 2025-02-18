ask - crypto - server / app / static / js / scripts.js;
const cryptoPricesDiv = document.getElementById("crypto-prices");
const stablecoinPricesDiv = document.getElementById("stablecoin-prices");

const ws = new WebSocket("ws://localhost:8765");
ws.onopen = () => {
  ws.send(JSON.stringify({ type: "crypto" }));
  ws.send(JSON.stringify({ type: "stablecoin" }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data[0].exchange) {
    cryptoPricesDiv.innerHTML = JSON.stringify(data, null, 2);
  } else {
    stablecoinPricesDiv.innerHTML = JSON.stringify(data, null, 2);
  }
};
