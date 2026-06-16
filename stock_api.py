import yfinance as yf
import pandas as pd
import requests

def fetch_stock_data(symbol, period="2y", interval="1d"):
    """
    פונקציה זו שואבת היסטוריית מסחר מ-Yahoo Finance,
    עוקפת חסימות ענן, ומנקה נתונים חסרים (NaN).
    """
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        ticker = yf.Ticker(symbol, session=session)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            print(f"No data found or blocked by Yahoo for symbol: {symbol}")
            return pd.DataFrame()

        df = df.reset_index()

        if 'Date' in df.columns:
            df = df.rename(columns={'Date': 'Time'})
        elif 'Datetime' in df.columns:
            df = df.rename(columns={'Datetime': 'Time'})

        columns_to_keep = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        available_columns = [col for col in columns_to_keep if col in df.columns]
        df = df[available_columns]

        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

        # התיקון הקריטי: מחיקת שורות שבהן חסר מחיר סגירה
        df = df.dropna(subset=['Close'])

        return df

    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    print("Test: Fetching AAPL stock data...")
    test_df = fetch_stock_data("AAPL")
    if not test_df.empty:
        print(test_df.tail())
    else:
        print("Failed to fetch data.")