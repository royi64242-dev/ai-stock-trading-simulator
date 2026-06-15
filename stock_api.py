import yfinance as yf
import pandas as pd


def fetch_stock_data(symbol, period="2y", interval="1d"):
    """
    פונקציה זו שואבת היסטוריית מסחר מ-Yahoo Finance עבור מניה ספציפית,
    ומחזירה טבלת Pandas במבנה אחיד ותואם לקריפטו.
    """
    try:
        ticker_data = yf.download(symbol, period=period, interval=interval)

        if ticker_data.empty:
            print(f"No data found for symbol: {symbol}")
            return pd.DataFrame()

        df = ticker_data.reset_index()

        df = df.rename(columns={'Date': 'Time'})

        columns_to_keep = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        df = df[columns_to_keep]

        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

        return df

    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame()



if __name__ == "__main__":
    print("Test: Fetching AAPL stock data...")
    test_df = fetch_stock_data("AAPL")
    print(test_df.head())