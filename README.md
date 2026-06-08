# 📈 AI Algo-Trading Simulator API

A dynamic, real-time stock market simulation API powered by Machine Learning. 

This project allows users to simulate stock trading using live market data while receiving dynamic Long/Short recommendations from an integrated AI Advisor.

## 🚀 Key Features
* **Live Market Data:** Integrates with Yahoo Finance (`yfinance`) to fetch real-time stock prices.
* **Dynamic AI Advisor:** Utilizes `scikit-learn`'s Linear Regression model, trained on-the-fly on 1-year historical data, to predict next-day price movements and provide actionable recommendations.
* **Portfolio Management:** Tracks user balances, active stock holdings, and calculates live net worth.
* **Cloud-Ready MLOps:** Containerized using Docker and served via a robust FastAPI backend.

## 🛠️ Tech Stack
* **Backend:** Python, FastAPI, Uvicorn
* **Data Science & ML:** Pandas, NumPy, Scikit-Learn
* **Financial Data:** yfinance
* **Deployment:** Docker

## 🚧 Work in Progress / Roadmap
This project is continuously evolving. Planned upcoming features include:
- [ ] Integration of more complex ML models (e.g., Random Forest, LSTM).
- [ ] Advanced performance visualizations and charting capabilities.
- [ ] User authentication and database integration for persistent portfolio storage.
- [ ] Frontend UI to complement the FastAPI backend.

## 💻 How to Run Locally

1. Clone the repository:
   ```bash
   git clone [https://github.com/YourUsername/ai-algo-trading-api.git](https://github.com/YourUsername/ai-algo-trading-api.git)

2. Install dependencies:
   ```bash
    pip install -r requirements.txt

3. Run the server: 
    ```bash
    uvicorn main:app --reload
   
4. Open http://127.0.0.1:8000/docs in your browser to interact with the API.
    