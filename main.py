import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse


# ==========================================
# 1. Core Logic Classes (Market & Portfolio)
# ==========================================

class Market:
    def get_live_price(self, stock_symbol: str) -> float:
        try:
            ticker = yf.Ticker(stock_symbol)
            # Using history is generally more stable on cloud servers than fast_info
            hist = ticker.history(period="1d")
            if hist.empty:
                return None
            return round(hist['Close'].iloc[-1], 2)
        except Exception:
            return None

    def get_ai_recommendation(self, stock_symbol: str):
        ticker = yf.Ticker(stock_symbol)
        hist = ticker.history(period="1y")

        if hist.empty:
            return {"error": f"No historical data found for {stock_symbol}."}

        current_price = self.get_live_price(stock_symbol)
        if current_price is None:
            return {"error": f"Could not fetch live price for {stock_symbol}."}

        hist['Day'] = np.arange(len(hist))
        X = hist[['Day']].values
        y = hist['Close'].values

        model = LinearRegression()
        model.fit(X, y)

        next_day_num = np.array([[len(hist)]])
        predicted_price = model.predict(next_day_num)[0]

        action = "LONG / BUY" if predicted_price > current_price else "SHORT / SELL"

        return {
            "ticker": stock_symbol,
            "current_price": round(current_price, 2),
            "predicted_price_tomorrow": round(predicted_price, 2),
            "recommendation": action
        }


class Portfolio:
    def __init__(self, initial_balance):
        self.balance = initial_balance
        self.holdings = {}

    def buy(self, stock: str, quantity: int, market: Market):
        current_price = market.get_live_price(stock)
        if current_price is None:
            return {"error": "Stock not found or API error."}

        total_cost = current_price * quantity
        if total_cost > self.balance:
            return {"error": f"Insufficient funds. Need ${total_cost:.2f}."}

        self.balance -= total_cost
        self.holdings[stock] = self.holdings.get(stock, 0) + quantity
        return {"message": f"Successfully bought {quantity} shares of {stock} at ${current_price:.2f}"}

    def sell(self, stock: str, quantity: int, market: Market):
        if stock in self.holdings and self.holdings[stock] >= quantity:
            current_price = market.get_live_price(stock)
            if current_price is None:
                return {"error": "Could not fetch live price for sale."}

            total_revenue = current_price * quantity
            self.balance += total_revenue
            self.holdings[stock] -= quantity

            if self.holdings[stock] == 0:
                del self.holdings[stock]

            return {"message": f"Successfully sold {quantity} shares of {stock} at ${current_price:.2f}"}
        else:
            return {"error": f"You don't own {quantity} shares of {stock}!"}

    def get_summary(self, market: Market):
        total_stocks_value = 0
        holdings_details = {}

        for stock, quantity in self.holdings.items():
            price = market.get_live_price(stock)
            if price:
                val = quantity * price
                total_stocks_value += val
                # Keys strictly matched to exactly what the JS frontend expects
                holdings_details[stock] = {"quantity": quantity, "current_price": price, "total_value": val}

        return {
            "cash": round(self.balance, 2),
            "net_worth": round(self.balance + total_stocks_value, 2),
            "holdings": holdings_details
        }


# ==========================================
# 2. FastAPI Setup & Routes
# ==========================================

app = FastAPI(
    title="AI Algo-Trading Simulator API",
    description="Live trading simulator with Dynamic Linear Regression predictions.",
    version="1.0.0"
)

# Global instances memory (resets on server restart)
live_market = Market()
my_portfolio = Portfolio(10000.0)


# Pydantic model matches frontend JSON exactly
class TradeRequest(BaseModel):
    ticker: str
    quantity: int


@app.post("/trade/buy")
def buy_stock(request: TradeRequest):
    return my_portfolio.buy(request.ticker.upper(), request.quantity, live_market)


@app.post("/trade/sell")
def sell_stock(request: TradeRequest):
    return my_portfolio.sell(request.ticker.upper(), request.quantity, live_market)


@app.get("/portfolio")
def get_portfolio():
    return my_portfolio.get_summary(live_market)


@app.get("/ai-advisor/{stock_symbol}")
def get_ai_prediction(stock_symbol: str):
    result = live_market.get_ai_recommendation(stock_symbol.upper())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ==========================================
# 3. Web Frontend (HTML UI)
# ==========================================

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html dir="ltr">
    <head>
        <meta charset="utf-8">
        <title>AI Trading Simulator</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: white; text-align: center; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }
            .card { background-color: #1e1e1e; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: left; }
            h1, h2 { text-align: center; color: #00ffcc; margin-top: 0; }
            input { padding: 10px; font-size: 16px; border-radius: 6px; border: none; outline: none; margin: 5px; width: calc(50% - 22px); background: #333; color: white; }
            button { padding: 12px 20px; font-size: 16px; background-color: #00ffcc; color: black; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; margin-top: 10px; transition: 0.2s;}
            button:hover { background-color: #00ccaa; }
            .sell-btn { background-color: #ff4444; color: white; }
            .sell-btn:hover { background-color: #cc0000; }
            .result-box { margin-top: 15px; padding: 15px; background-color: #2a2a2a; border-radius: 8px; font-size: 16px; display: none; }
            .portfolio-item { display: flex; justify-content: space-between; border-bottom: 1px solid #444; padding: 8px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 AI Trading Simulator</h1>

            <div class="card">
                <h2>1. Ask AI Advisor</h2>
                <div style="display: flex; justify-content: center;">
                    <input type="text" id="aiTicker" placeholder="Symbol (e.g. TSLA)" autocomplete="off" style="width: 100%; text-align: center;" />
                </div>
                <button onclick="getPrediction()">Analyze Prediction</button>
                <div id="aiResult" class="result-box" style="text-align: center;"></div>
            </div>

            <div class="card">
                <h2>2. Trade Stocks</h2>
                <div style="display: flex; justify-content: space-between;">
                    <input type="text" id="tradeTicker" placeholder="Symbol (e.g. AAPL)" autocomplete="off" />
                    <input type="number" id="tradeQty" placeholder="Quantity" min="1" />
                </div>
                <div style="display: flex; gap: 10px;">
                    <button onclick="executeTrade('buy')">Buy Stock</button>
                    <button class="sell-btn" onclick="executeTrade('sell')">Sell Stock</button>
                </div>
                <div id="tradeResult" class="result-box" style="text-align: center;"></div>
            </div>

            <div class="card">
                <h2>3. Portfolio & Net Worth</h2>
                <button onclick="viewPortfolio()" style="background-color: #4a90e2; color: white;">Refresh Portfolio Data</button>
                <div id="portfolioResult" class="result-box"></div>
            </div>
        </div>

        <script>
            async function getPrediction() {
                const stock = document.getElementById('aiTicker').value.toUpperCase();
                const resDiv = document.getElementById('aiResult');
                if (!stock) return;
                resDiv.style.display = 'block'; resDiv.innerHTML = '⏳ Analyzing...';

                try {
                    const response = await fetch('/ai-advisor/' + stock);
                    const data = await response.json();
                    if (!response.ok || data.detail) {
                        resDiv.innerHTML = '❌ Server Error: ' + (data.detail || 'Endpoint missing'); return;
                    }
                    if (data.error) {
                        resDiv.innerHTML = '❌ ' + data.error;
                    } else {
                        const isBuy = data.recommendation.includes('BUY');
                        resDiv.innerHTML = `<h3>${data.ticker}: $${data.current_price}</h3>
                                            <p style="color: ${isBuy ? '#00ffcc' : '#ff4444'}; font-weight: bold; font-size: 20px;">${data.recommendation}</p>`;
                    }
                } catch (e) { resDiv.innerHTML = '❌ Connection Error'; }
            }

            async function executeTrade(action) {
                const ticker = document.getElementById('tradeTicker').value.toUpperCase();
                const qty = parseInt(document.getElementById('tradeQty').value);
                const resDiv = document.getElementById('tradeResult');
                if (!ticker || isNaN(qty) || qty <= 0) {
                    resDiv.style.display = 'block'; resDiv.innerHTML = '⚠️ Invalid input'; return;
                }

                resDiv.style.display = 'block'; resDiv.innerHTML = '⏳ Executing trade...';

                try {
                    const response = await fetch('/trade/' + action, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ticker: ticker, quantity: qty })
                    });
                    const data = await response.json();

                    if (data.error) {
                        resDiv.innerHTML = `<span style="color: #ff4444;">❌ ${data.error}</span>`;
                    } else {
                        resDiv.innerHTML = `<span style="color: #00ffcc;">✅ ${data.message}</span>`;
                        viewPortfolio(); // Auto-refresh portfolio after trade
                    }
                } catch (e) { resDiv.innerHTML = '❌ Connection Error'; }
            }

            async function viewPortfolio() {
                const resDiv = document.getElementById('portfolioResult');
                resDiv.style.display = 'block'; resDiv.innerHTML = '⏳ Fetching live prices...';

                try {
                    const response = await fetch('/portfolio');
                    const data = await response.json();

                    let html = `<h3>Total Net Worth: <span style="color: #00ffcc;">$${data.net_worth.toLocaleString()}</span></h3>`;
                    html += `<p>Cash Balance: $${data.cash.toLocaleString()}</p><hr style="border:1px solid #444;">`;

                    if (Object.keys(data.holdings).length === 0) {
                        html += `<p style="text-align:center; color:#888;">Portfolio is empty.</p>`;
                    } else {
                        for (const [ticker, info] of Object.entries(data.holdings)) {
                            const percent = ((info.total_value / data.net_worth) * 100).toFixed(1);
                            html += `
                            <div class="portfolio-item">
                                <div><b>${ticker}</b> (${info.quantity} shares)</div>
                                <div>$${info.total_value.toLocaleString()}</div>
                            </div>
                            <div style="width: 100%; background: #444; height: 6px; margin-bottom: 10px; border-radius: 3px;">
                                <div style="width: ${percent}%; background: #00ffcc; height: 100%; border-radius: 3px;"></div>
                            </div>
                            <small style="color: #aaa;">Current Price: $${info.current_price} | ${percent}% of portfolio</small>
                            <br><br>`;
                        }
                    }
                    resDiv.innerHTML = html;
                } catch (e) { resDiv.innerHTML = '❌ Connection Error'; }
            }
        </script>
    </body>
    </html>
    """