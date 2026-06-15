import pandas as pd
import numpy as np
import xgboost as xgb


def analyze_asset(df, asset_name):
    print(f"\n🧠 Initiating AI Training Engine for {asset_name}...")

    # ==========================================
    # 1. Feature Engineering (יצירת אינדיקטורים)
    # ==========================================
    # חישוב ממוצעים נעים ואחוזי שינוי. rolling עובר על חלון של X ימים אחורה.
    df['MA200'] = df['Close'].rolling(window=200).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['Return'] = df['Close'].pct_change()
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()

    # אלו התכונות (עמודות) שהמודל יסתכל עליהן כדי לקבל החלטה
    features = ['Close', 'MA200', 'MA50', 'Return', 'Volume', 'Vol_MA20']

    # הכנת הנתונים של *היום*. זו השורה האחרונה בטבלה.
    # המודל דורש לקבל נתונים במבנה דו-ממדי (טבלה), אז אנחנו משתמשים ב-reshape.
    current_features = df[features].iloc[-1].values.reshape(1, -1)
    current_price = df['Close'].iloc[-1]

    # ==========================================
    # 2. הגדרת חלונות הזמן לעתיד
    # ==========================================
    # מכיוון שכל שורה בטבלה היא יום אחד (1d), 30 שורות קדימה = חודש.
    horizons = {'1 Month': 30, '6 Months': 180, '12 Months': 365}

    print("\n==========================================")
    print(f"📊 AI Market Analysis for {asset_name}")
    print("==========================================")
    print(f"Current Price: ${current_price:,.2f}\n")

    # ==========================================
    # 3. אימון וחיזוי לכל טווח זמן בנפרד
    # ==========================================
    for name, days in horizons.items():
        # עותק נקי של הטבלה לכל לולאה
        df_train = df.copy()

        # יצירת מטרת הלמידה (Target): "תמשוך את המחיר שיהיה בעוד X ימים אחורה להיום"
        df_train['Target'] = df_train['Close'].shift(-days)

        # ניקוי שורות חסרות (NaN).
        # למשל, ל-365 הימים האחרונים בטבלה עוד אין עתיד של שנה, ולכן הם יימחקו משלב הלמידה.
        df_model = df_train[features + ['Target']].dropna()

        # בקרת איכות: האם יש בכלל מספיק היסטוריה למטבע/מניה הזו?
        if df_model.empty or len(df_model) < 50:
            print(f"Timeline: {name} - ⚠️ Not enough historical data to predict.")
            print("------------------------------------------")
            continue

        # חלוקה ל-X (חומר הלימוד) ו-y (דף התשובות)
        X_train = df_model[features].values
        y_train = df_model['Target'].values

        # הקמה ואימון של אלגוריתם ה-XGBoost
        model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
        model.fit(X_train, y_train)

        # רגע האמת: מבקשים מהמודל לחזות את המחיר לפי הנתונים של *היום*
        pred_price = model.predict(current_features)[0]

        # מתמטיקה פשוטה: חישוב אחוז העלייה/ירידה הצפוי
        change_pct = ((pred_price - current_price) / current_price) * 100

        # קבלת החלטה - ממליצים לקנות רק אם צפויה עלייה של מעל 5%
        action = "BUY 🟢" if change_pct > 5 else "HOLD / SELL 🔴"

        print(f"Timeline: {name}")
        print(f"Predicted Price: ${pred_price:,.2f} ({change_pct:+.2f}%)")
        print(f"Recommendation: {action}")
        print("------------------------------------------")