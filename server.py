import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
import xgboost as xgb

from crypto_api import fetch_crypto_data
from stock_api import fetch_stock_data

app = FastAPI(title="AI Algo-Trading Simulator (XGBoost Edition)")

# חיבור תיקיית הקבצים הסטטיים לפרונטאנד
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# פונקציית עזר להרצת מודל ה-XGBoost והחזרת נתונים מובנים לפרונטאנד
def generate_xgboost_predictions(df):
    df = df.copy()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['Return'] = df['Close'].pct_change()
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()

    features = ['Close', 'MA200', 'MA50', 'Return', 'Volume', 'Vol_MA20']
    current_features = df[features].iloc[-1].values.reshape(1, -1)
    current_price = float(df['Close'].iloc[-1])

    horizons = {'1 Month': 30, '6 Months': 180, '12 Months': 365}
    predictions_list = []

    for name, days in horizons.items():
        df_train = df.copy()
        df_train['Target'] = df_train['Close'].shift(-days)
        df_model = df_train[features + ['Target']].dropna()

        if df_model.empty or len(df_model) < 50:
            continue

        X_train = df_model[features].values
        y_train = df_model['Target'].values

        model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
        model.fit(X_train, y_train)

        pred_price = float(model.predict(current_features)[0])
        change_pct = ((pred_price - current_price) / current_price) * 100
        action = "BUY 🟢" if change_pct > 5 else "HOLD / SELL 🔴"

        predictions_list.append({
            "timeline": name,
            "predicted_price": round(pred_price, 2),
            "change_pct": round(change_pct, 2),
            "recommendation": action
        })

    return current_price, predictions_list


# פונקציית עזר לחילוץ מחיר עדכני עבור סימולטור המסחר והתיק
def get_live_price(symbol: str) -> float:
    try:
        df = fetch_crypto_data(f"{symbol}USDT", limit=5)
        if not df.empty:
            return float(df['Close'].iloc[-1])
    except:
        pass
    try:
        df = fetch_stock_data(symbol)
        if not df.empty:
            return float(df['Close'].iloc[-1])
    except:
        pass
    return None


# ניהול תיק ההשקעות בזיכרון השרת
class Portfolio:
    def __init__(self, initial_balance):
        self.balance = initial_balance
        self.holdings = {}

    def buy(self, stock: str, quantity: int):
        current_price = get_live_price(stock)
        if current_price is None:
            return {"error": "Asset not found or API error."}
        total_cost = current_price * quantity
        if total_cost > self.balance:
            return {"error": f"Insufficient funds. Need ${total_cost:.2f}."}
        self.balance -= total_cost
        self.holdings[stock] = self.holdings.get(stock, 0) + quantity
        return {"message": f"Successfully bought {quantity} units of {stock} at ${current_price:.2f}"}

    def sell(self, stock: str, quantity: int):
        if stock in self.holdings and self.holdings[stock] >= quantity:
            current_price = get_live_price(stock)
            if current_price is None:
                return {"error": "Could not fetch live price for sale."}
            total_revenue = current_price * quantity
            self.balance += total_revenue
            self.holdings[stock] -= quantity
            if self.holdings[stock] == 0:
                del self.holdings[stock]
            return {"message": f"Successfully sold {quantity} units of {stock} at ${current_price:.2f}"}
        else:
            return {"error": f"You don't own {quantity} units of {stock}!"}

    def get_summary(self):
        total_value = 0
        holdings_details = {}
        for stock, quantity in self.holdings.items():
            price = get_live_price(stock)
            if price:
                val = quantity * price
                total_value += val
                holdings_details[stock] = {"quantity": quantity, "current_price": price, "total_value": val}
        return {
            "cash": round(self.balance, 2),
            "net_worth": round(self.balance + total_value, 2),
            "holdings": holdings_details
        }


my_portfolio = Portfolio(10000.0)


class TradeRequest(BaseModel):
    ticker: str
    quantity: int


# ניתוב עמוד הבית לפרונטאנד הסטטי
@app.get("/", response_class=HTMLResponse)
def read_root():
    if os.path.exists("static/index.html"):
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Static index.html not found in static/ folder.</h1>"


# אנדפוינט הניתוח והחיזוי המשולב
@app.get("/api/ai-advisor/{asset_type}/{symbol}")
def get_ai_prediction(asset_type: str, symbol: str):
    symbol = symbol.upper().strip()
    if asset_type == "crypto":
        df = fetch_crypto_data(f"{symbol}USDT")
    else:
        df = fetch_stock_data(symbol)

    if df.empty:
        raise HTTPException(status_code=400, detail=f"No data found for {symbol}.")

    try:
        current_price, predictions = generate_xgboost_predictions(df)
        return {
            "ticker": symbol,
            "current_price": current_price,
            "predictions": predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# אנדפוינטס למסחר וניהול תיק
@app.post("/api/trade/buy")
def buy_asset(request: TradeRequest):
    return my_portfolio.buy(request.ticker.upper().strip(), request.quantity)


@app.post("/api/trade/sell")
def sell_asset(request: TradeRequest):
    return my_portfolio.sell(request.ticker.upper().strip(), request.quantity)


@app.get("/api/portfolio")
def get_portfolio():
    return my_portfolio.get_summary()