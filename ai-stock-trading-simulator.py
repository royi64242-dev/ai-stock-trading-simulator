import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


class Market:

    def __init__(self):
        self.cache = {}  # Simple cache to avoid spamming Yahoo Finance too often

    def get_live_price(self, stock_symbol: str) -> float:
        try:
            ticker = yf.Ticker(stock_symbol)
            current_price = ticker.fast_info['lastPrice']
            return round(current_price, 2)
        except Exception:
            return None

    def get_ai_recommendation(self, stock_symbol: str):

        print(f"\n[AI] Fetching historical data and analyzing {stock_symbol}...")
        ticker = yf.Ticker(stock_symbol)

        hist = ticker.history(period="1y")
        if hist.empty:
            print(f"❌ AI Note: No historical data found for {stock_symbol}.")
            return

        current_price = self.get_live_price(stock_symbol)
        if current_price is None:
            print(f"❌ AI Note: Could not fetch live price for {stock_symbol}.")
            return

        hist['Day'] = np.arange(len(hist))
        X = hist[['Day']].values
        y = hist['Close'].values

        model = LinearRegression()
        model.fit(X, y)

        next_day_num = np.array([[len(hist)]])
        predicted_price = model.predict(next_day_num)[0]

        margin_pct = ((predicted_price - current_price) / current_price) * 100

        print(f"\n=== AI Advisor Analysis for {stock_symbol} ===")
        print(f"Current Live Price:  ${current_price:.2f}")
        print(f"Predicted Tomorrow:  ${predicted_price:.2f}")
        print(f"Expected Move:       {margin_pct:.2f}%")

        if predicted_price > current_price:
            print("Recommendation: 🟢 LONG / BUY (Upward trend expected)")
        else:
            print("Recommendation: 🔴 SHORT / SELL (Downward trend expected)")


class Portfolio:

    def __init__(self, initial_balance):
        self.balance = initial_balance
        self.holdings = {}
        self.transaction_history = []

    def buy(self, stock: str, amount: int, market: Market):
        current_price = market.get_live_price(stock)

        if current_price is None:
            print("❌ Transaction declined: Stock not found or API error.")
            return

        total_cost = current_price * amount
        if total_cost > self.balance:
            print(f"❌ Transaction declined: Insufficient funds. You need ${total_cost:.2f}.")
        else:
            self.balance -= total_cost
            self.holdings[stock] = self.holdings.get(stock, 0) + amount
            self.transaction_history.append(("BUY", stock, amount, current_price))
            print(f"✅ Successfully bought {amount} shares of {stock} at ${current_price:.2f} each!")

    def sell(self, stock: str, amount: int, market: Market):
        if stock in self.holdings and self.holdings[stock] >= amount:
            current_price = market.get_live_price(stock)

            if current_price is None:
                print("❌ Transaction declined: Could not fetch live price for sale.")
                return

            total_revenue = current_price * amount
            self.balance += total_revenue
            self.holdings[stock] -= amount

            if self.holdings[stock] == 0:
                del self.holdings[stock]

            self.transaction_history.append(("SELL", stock, amount, current_price))
            print(f"✅ Successfully sold {amount} shares of {stock} at ${current_price:.2f} each!")
        else:
            print("❌ Transaction declined: You don't own enough shares of this stock.")

    def get_net_worth(self, market: Market) -> float:
        total_stocks_value = 0
        for stock, amount in self.holdings.items():
            price = market.get_live_price(stock)
            if price is not None:
                total_stocks_value += (price * amount)
        return self.balance + total_stocks_value

    def view(self, market: Market):
        print("\n--- Your Portfolio ---")
        if not self.holdings:
            print("You don't own any shares yet.")
            total_stocks_value = 0
        else:
            total_stocks_value = 0
            for stock, amount in self.holdings.items():
                current_price = market.get_live_price(stock)
                if current_price:
                    stock_value = amount * current_price
                    total_stocks_value += stock_value
                    print(
                        f"• {stock} | Shares: {amount} | Live Price: ${current_price:.2f} | Total Value: ${stock_value:.2f}")
                else:
                    print(f"• {stock} | Shares: {amount} | Live Price: ERROR FETCHING DATA")

        print(f"\nTotal Stocks Value: ${total_stocks_value:.2f}")
        print(f"Free Cash Balance:  ${self.balance:.2f}")
        print(f"Total Net Worth:    ${self.balance + total_stocks_value:.2f}")

    def plot_allocation(self, market: Market):
        labels = ['Free Cash']
        sizes = [self.balance]

        for stock, amount in self.holdings.items():
            price = market.get_live_price(stock)
            if price:
                total_stock_value = price * amount
                labels.append(f"{stock} ({amount} shares)")
                sizes.append(total_stock_value)

        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 8))

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            startangle=140,
            textprops=dict(color="w", fontsize=10)
        )

        ax.set_title("Portfolio Allocation (Holdings vs. Cash)", fontsize=16, fontweight='bold')

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    live_market = Market()
    my_portfolio = Portfolio(10000.0)

    print("==================================================")
    print(" Welcome to AI Algo-Trading Simulator (Live Data) ")
    print("==================================================")

    while True:
        print("\n--- Main Menu ---")
        print("1 - Search & Buy Stock")
        print("2 - Sell Stock")
        print("3 - View Portfolio & Net Worth")
        print("4 - Ask AI Advisor (Live Data Prediction)")
        print("5 - Show Portfolio Allocation (Pie Chart)")
        print("6 - Exit Game")

        choice = input("Please choose an option: ")

        if choice == "6":
            final_net_worth = my_portfolio.get_net_worth(live_market)
            print(f"\nThanks for trading! Your final Net Worth is: ${final_net_worth:.2f}")
            break

        elif choice == "1":
            stock = input("Enter stock symbol (e.g., AAPL, NVDA): ").upper()
            price = live_market.get_live_price(stock)

            if price:
                print(f"Current price for {stock} is ${price:.2f}")
                try:
                    amount = int(input("Enter amount of shares to buy: "))
                    my_portfolio.buy(stock, amount, live_market)
                except ValueError:
                    print("❌ Invalid input. Please enter a whole number.")
            else:
                print("❌ Stock not found or API error.")

        elif choice == "2":
            if not my_portfolio.holdings:
                print("You have no stocks to sell.")
                continue

            print(f"Your holdings: {list(my_portfolio.holdings.keys())}")
            stock = input("Enter stock symbol to sell: ").upper()
            try:
                amount = int(input("Enter amount of shares to sell: "))
                my_portfolio.sell(stock, amount, live_market)
            except ValueError:
                print("❌ Invalid input. Please enter a whole number.")

        elif choice == "3":
            print("\nUpdating prices... Please wait.")
            my_portfolio.view(live_market)

        elif choice == "4":
            stock = input("Which stock should the AI analyze? ").upper()
            live_market.get_ai_recommendation(stock)

        elif choice == "5":
            print("\nGenerating Allocation Chart...")
            my_portfolio.plot_allocation(live_market)

        else:
            print("❌ Invalid choice, please try again.")

