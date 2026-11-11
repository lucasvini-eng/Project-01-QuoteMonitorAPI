import os
import sqlite3
import random
from datetime import datetime
import pandas as pd

DB_FILE = os.getenv("DATABASE_PATH", "quotes.db")
SHEETS_XLSX_URL = os.getenv(
    "SHEETS_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQx6J04PIEGYPmHyx4104LC92FrUsjNLQIy5kwISP53dfIX2qtNTx1KTmGPwZJmZm0a0BWkkAzJZvJ3/pub?output=xlsx"
)

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                currency TEXT NOT NULL,
                quote_value REAL NOT NULL,
                percent_change REAL NOT NULL,
                raw_date TEXT,
                raw_quote TEXT,
                raw_percent TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(datetime, currency) ON CONFLICT REPLACE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_currency ON quotes(currency)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_datetime ON quotes(datetime)")
        conn.commit()

def clean_numeric(val_str, symbol=None):
    if val_str is None or pd.isna(val_str):
        return None

    if isinstance(val_str, (int, float)):
        val = float(val_str)
    else:
        s = str(val_str).replace("R$", "").replace("$", "").replace(" ", "").strip()
        if not s:
            return None

        if "." in s and "," in s:
            if s.find(".") < s.find(","):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            s = s.replace(",", ".")
        elif "." in s:
            parts = s.split(".")
            if len(parts) == 2 and len(parts[1]) == 3 and symbol in ["BTC", "ETH"]:
                s = s.replace(".", "")

        try:
            val = float(s)
        except ValueError:
            return None

    if val is None:
        return None

    if symbol in ["USD", "EUR"]:
        if val >= 10000:
            val /= 10000.0
        elif val >= 100:
            val /= 100.0
    elif symbol == "CNY":
        if val >= 1000:
            val /= 10000.0
        elif val >= 10:
            val /= 100.0
    elif symbol == "BTC":
        if val < 1000:
            val *= 1000.0
    elif symbol == "ETH":
        if val < 500:
            val *= 1000.0
    else:
        if 50 < val < 1000:
            val /= 100.0
        elif 10000 <= val < 100000:
            val /= 10000.0

    return val

def clean_percentage(perc_str):
    if perc_str is None or pd.isna(perc_str):
        return 0.0

    if isinstance(perc_str, (int, float)):
        val = float(perc_str)
    else:
        s = str(perc_str).replace("%", "").replace("+", "").replace("(", "").replace(")", "").strip()
        if not s:
            return 0.0
        if "." in s and "," in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            val = float(s)
        except ValueError:
            return 0.0

    if abs(val) >= 20.0:
        val /= 100.0

    return val

def parse_date(dt_str):
    if dt_str is None or pd.isna(dt_str):
        return None
    if isinstance(dt_str, (datetime, pd.Timestamp)):
        return dt_str

    dt_str = str(dt_str).strip()
    formats = [
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            pass
    return None

def generate_mock_data():
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    mock_data = []
    currencies = [
        ("USD", 5.45, 0.05),
        ("EUR", 5.92, 0.04),
        ("CNY", 0.76, 0.01),
        ("BTC", 350000.0, 2500.0),
        ("ETH", 18500.0, 150.0)
    ]

    for dt in dates:
        dt_str = dt.strftime("%d/%m/%Y %H:%M:%S")
        for symbol, base_val, std in currencies:
            val = round(base_val + random.uniform(-std, std), 4 if symbol != "BTC" else 2)
            perc = round(random.uniform(-1.5, 1.8), 2)
            perc_str = f"{perc:+.2f}%".replace(".", ",")
            mock_data.append({
                "DATA": dt_str,
                "MOEDA": symbol,
                "COTAÇÃO": str(val).replace(".", ","),
                "PERCENTUAL": perc_str
            })

    return pd.DataFrame(mock_data)

def sync_sheets_to_sqlite(sheets_url: str = None) -> dict:
    init_db()
    url = sheets_url or SHEETS_XLSX_URL
    source = "google_sheets"
    error_note = None

    try:
        df_raw = pd.read_excel(url)
    except Exception as e:
        df_raw = generate_mock_data()
        source = "mock_contingency"
        error_note = str(e)

    if df_raw.empty or "DATA" not in df_raw.columns:
        return {"status": "error", "message": "Planilha sem colunas válidas", "source": source}

    records_to_insert = []
    for _, row in df_raw.iterrows():
        dt = parse_date(row.get("DATA"))
        if not dt:
            continue
        dt_iso = dt.strftime("%Y-%m-%d %H:%M:%S")
        currency = str(row.get("MOEDA", "")).strip().upper()
        raw_quote = str(row.get("COTAÇÃO", ""))
        raw_percent = str(row.get("PERCENTUAL", ""))

        quote_val = clean_numeric(raw_quote, currency)
        percent_val = clean_percentage(raw_percent)

        if quote_val is not None:
            records_to_insert.append((
                dt_iso,
                currency,
                quote_val,
                percent_val,
                str(row.get("DATA")),
                raw_quote,
                raw_percent
            ))

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO quotes (
                datetime, currency, quote_value, percent_change,
                raw_date, raw_quote, raw_percent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(datetime, currency) DO UPDATE SET
                quote_value = excluded.quote_value,
                percent_change = excluded.percent_change,
                raw_date = excluded.raw_date,
                raw_quote = excluded.raw_quote,
                raw_percent = excluded.raw_percent
        """, records_to_insert)
        conn.commit()

    return {
        "status": "success",
        "source": source,
        "processed_records": len(records_to_insert),
        "note": error_note
    }

def get_quotes(currency=None, start_date=None, end_date=None, limit=None):
    init_db()
    query = "SELECT id, datetime, currency, quote_value, percent_change, raw_date, raw_quote, raw_percent FROM quotes WHERE 1=1"
    params = []

    if currency:
        query += " AND currency = ?"
        params.append(currency.upper())

    if start_date:
        query += " AND datetime >= ?"
        params.append(f"{start_date} 00:00:00" if len(start_date) == 10 else start_date)

    if end_date:
        query += " AND datetime <= ?"
        params.append(f"{end_date} 23:59:59" if len(end_date) == 10 else end_date)

    query += " ORDER BY datetime ASC"

    if limit:
        query += " LIMIT ?"
        params.append(int(limit))

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_latest_quotes():
    init_db()
    query = """
        SELECT q.id, q.datetime, q.currency, q.quote_value, q.percent_change,
               q.raw_date, q.raw_quote, q.raw_percent
        FROM quotes q
        INNER JOIN (
            SELECT currency, MAX(datetime) as max_dt
            FROM quotes
            GROUP BY currency
        ) latest ON q.currency = latest.currency AND q.datetime = latest.max_dt
        ORDER BY q.currency ASC
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_available_currencies():
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT currency FROM quotes ORDER BY currency ASC")
        return [row[0] for row in cursor.fetchall()]

def count_quotes():
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM quotes")
        return cursor.fetchone()[0]
