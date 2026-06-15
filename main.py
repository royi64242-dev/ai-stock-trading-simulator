import sys

# מייבאים את הפונקציות שבנינו מתוך הקבצים הנפרדים שלהן
from crypto_api import fetch_crypto_data
from stock_api import fetch_stock_data


# בעתיד נשחרר את השורה הזו מהערה כשנסיים לבנות את המודל:
# from ai_model import analyze_asset

def main():
    print("==========================================")
    print("🚀 AI Algo-Trading Router (Modular System)")
    print("==========================================")

    # 1. קבלת החלטה מהמשתמש (הניתוב)
    print("What market would you like to analyze?")
    print("1. Crypto (Binance)")
    print("2. US Stocks / ETFs (Yahoo Finance)")

    asset_type = input("\nEnter choice (1 or 2): ").strip()

    # 2. הפעלת "הפועל" המתאים לפי הבחירה
    if asset_type == '1':
        symbol = input("Enter Crypto symbol (e.g., BTC, ETH): ").strip().upper()
        # לקריפטו אנחנו מוסיפים USDT מאחורי הקלעים כדי להקל על המשתמש
        full_symbol = f"{symbol}USDT"
        print(f"\n📡 Fetching Crypto data for {full_symbol}...")
        df = fetch_crypto_data(full_symbol)

    elif asset_type == '2':
        symbol = input("Enter Stock/ETF symbol (e.g., AAPL, SPY, TQQQ): ").strip().upper()
        print(f"\n📡 Fetching Stock data for {symbol}...")
        df = fetch_stock_data(symbol)

    else:
        print("❌ Invalid choice. Please run again and select 1 or 2.")
        sys.exit()  # פקודה שעוצרת את התוכנית באלגנטיות

    # 3. מנגנון בקרת איכות (QA)
    if df.empty:
        print(f"⚠️ Could not fetch data for {symbol}. Check the symbol and your connection.")
        sys.exit()

    # 4. הצגת התוצר לראווה
    # בשלב הזה לא אכפת לנו אם זו מניה או קריפטו - הטבלה נראית בדיוק אותו הדבר!
    print("\n✅ Data pipeline successful! Standardized format ready for AI:")
    print(df.tail())

    # 5. תחנת הסיום - המסירה למוח המלאכותי
    # print("\n🧠 Sending data to AI Engine...")
    # analyze_asset(df, symbol)


if __name__ == "__main__":
    main()