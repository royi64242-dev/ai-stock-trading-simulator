FROM python:3.10-slim

WORKDIR /app

# התקנת כלים בסיסיים של מערכת ההפעלה שדרושים לחלק מספריות הנתונים
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# העתקה והתקנה של דרישות הקוד
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתקת כל שאר קבצי הפרויקט (כולל תיקיית static)
COPY . .

# חשיפת הפורט המתאים לעבודה בענן
EXPOSE 8000

# פקודת ההרצה של השרת באמצעות uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]