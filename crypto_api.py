import requests
import pandas as pd


def fetch_crypto_data(symbol, interval="1d", limit=1000):
    """
    פונקציה זו שואבת היסטוריית מסחר מבינאנס עבור מטבע ספציפי,
    ומחזירה טבלת Pandas מוכנה לניתוח.
    """

    url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            raw_data = response.json()

            columns_names = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']

            df = pd.DataFrame([row[0:6] for row in raw_data], columns=columns_names)

            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
            df['Time'] = pd.to_datetime(df['Time'], unit='ms')

            return df

        else:
            print(f"API Error: Binance returned status code {response.status_code}")
            return pd.DataFrame()

    except Exception as e:
        print(f"Network Connection Error: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    print("Test: Fetching ETHUSDT data...")
    test_df = fetch_crypto_data("ETHUSDT")
    print(test_df.head())