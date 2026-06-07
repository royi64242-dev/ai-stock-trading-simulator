import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


# ==========================================
# 1. Core Logic Classes (Market & Portfolio)
# ==========================================

class Market:
    def get_live_price(self, stock_symbol: str) -> float:
        try:
            ticker = yf.Ticker(stock_symbol)
            current_price = ticker.fast_info['lastPrice']
            return round(current_price, 2)
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
        margin_pct = ((predicted_price - current_price) / current_price) * 100

        action = "LONG / BUY" if predicted_price > current_price else "SHORT / SELL"

        # Return a dictionary instead of printing
        return {
            "ticker": stock_symbol,
            "current_price": round(current_price, 2),
            "predicted_price_tomorrow": round(predicted_price, 2),
            "expected_move_pct": round(margin_pct, 2),
            "recommendation": action
        }


class Portfolio:
    def __init__(self, initial_balance):
        self.balance = initial_balance
        self.holdings = {}

    def buy(self, stock: str, amount: int, market: Market):
        current_price = market.get_live_price(stock)
        if current_price is None:
            raise HTTPException(status_code=404, detail="Stock not found or API error.")

        total_cost = current_price * amount
        if total_cost > self.balance:
            raise HTTPException(status_code=400, detail=f"Insufficient funds. Need ${total_cost:.2f}.")

        self.balance -= total_cost
        self.holdings[stock] = self.holdings.get(stock, 0) + amount
        return {"status": "success", "message": f"Bought {amount} shares of {stock} at ${current_price:.2f}"}

    def sell(self, stock: str, amount: int, market: Market):
        if stock in self.holdings and self.holdings[stock] >= amount:
            current_price = market.get_live_price(stock)
            if current_price is None:
                raise HTTPException(status_code=500, detail="Could not fetch live price for sale.")

            total_revenue = current_price * amount
            self.balance += total_revenue
            self.holdings[stock] -= amount
            if self.holdings[stock] == 0:
                del self.holdings[stock]
            return {"status": "success", "message": f"Sold {amount} shares of {stock} at ${current_price:.2f}"}
        else:
            raise HTTPException(status_code=400, detail="Not enough shares to sell.")

    def get_summary(self, market: Market):
        total_stocks_value = 0
        holdings_details = {}
        for stock, amount in self.holdings.items():
            price = market.get_live_price(stock)
            if price:
                val = amount * price
                total_stocks_value += val
                holdings_details[stock] = {"shares": amount, "live_price": price, "total_value": val}

        return {
            "cash_balance": round(self.balance, 2),
            "stocks_value": round(total_stocks_value, 2),
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

# Initialize global game state
# Note: In production with multiple users, this would be stored in a database.
live_market = Market()
my_portfolio = Portfolio(10000.0)


# Define Pydantic models for request validation
class TradeRequest(BaseModel):
    stock_symbol: str
    amount: int


@app.get("/")
def root():
    return {"message": "Welcome to the AI Trading API. Navigate to /docs for the interactive UI."}


@app.get("/portfolio")
def get_portfolio():
    """Returns the current user balance and active stock holdings."""
    return my_portfolio.get_summary(live_market)


@app.post("/trade/buy")
def buy_stock(request: TradeRequest):
    """Executes a buy order at the current live market price."""
    return my_portfolio.buy(request.stock_symbol.upper(), request.amount, live_market)


@app.post("/trade/sell")
def sell_stock(request: TradeRequest):
    """Executes a sell order at the current live market price."""
    return my_portfolio.sell(request.stock_symbol.upper(), request.amount, live_market)


@app.get("/ai-advisor/{stock_symbol}")
def get_ai_prediction(stock_symbol: str):
    """Trains a Linear Regression model dynamically and returns a Long/Short recommendation."""
    result = live_market.get_ai_recommendation(stock_symbol.upper())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result