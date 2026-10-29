import os
import pandas as pd
from sqlalchemy import text
from pathlib import Path
def get_database_url():
    try:
        if "postgres" in __import__("streamlit").secrets:
            return __import__("streamlit").secrets["postgres"]["url"]
    except Exception:
        pass
    return os.getenv("DATABASE_URL")

def init_sqlite(engine):
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            stock_code TEXT PRIMARY KEY,
            description TEXT,
            category TEXT
        )
        """))
    # Make the demo immediately usable on a fresh local run or cloud deploy.
    count = pd.read_sql("SELECT COUNT(*) AS n FROM products", engine).iloc[0]["n"]
    if count == 0:
        demo_path = "data/sample_transactions.csv"
        if os.path.exists(demo_path):
            demo = pd.read_csv(demo_path)
            products = demo[["stock_code", "description"]].drop_duplicates("stock_code").copy()
            def category_for(description):
                d = str(description).upper()
                for category, words in {
                    "Dekorasi": ["CANDLE", "DECORATION", "STAR", "HOLDER"],
                    "Dapur": ["MUG", "CUP", "TEA"],
                    "Aksesori": ["NECKLACE", "BAG"],
                    "Alat Tulis": ["NOTEBOOK", "PEN"],
                    "Mainan": ["TOY", "PUZZLE"],
                    "Tekstil": ["CUSHION", "COVER"],
                }.items():
                    if any(word in d for word in words):
                        return category
                return "Lainnya"
            products["category"] = products["description"].apply(category_for)
            products.to_sql("products", engine, if_exists="append", index=False)

def init_postgres(engine):
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transactions (
            invoice_no TEXT,
            stock_code TEXT,
            quantity INTEGER,
            invoice_date TIMESTAMP,
            unit_price DOUBLE PRECISION,
            customer_id TEXT,
            country TEXT
        )
        """))

def load_joined_data(pg_engine, sqlite_engine, demo=False):
    products = pd.read_sql("SELECT stock_code, description, category FROM products", sqlite_engine)
    if pg_engine is not None and not demo:
        transactions = pd.read_sql("SELECT invoice_no, stock_code, quantity, invoice_date, unit_price, customer_id, country FROM transactions", pg_engine)
    else:
        # Demo mode is intentionally local and is not a substitute for the required PostgreSQL deployment.
        demo_path = Path(__file__).resolve().parent / "data" / "sample_transactions.csv"
        transactions = pd.read_csv(demo_path, parse_dates=["invoice_date"])
        if "description" not in products.columns and "description" in transactions.columns:
            pass
    transactions["stock_code"] = transactions["stock_code"].astype(str)
    products["stock_code"] = products["stock_code"].astype(str)
    # In the demo CSV description is included for convenience, but the reference table is authoritative.
    if "description" in transactions.columns:
        transactions = transactions.drop(columns=["description"])
    merged = transactions.merge(products, on="stock_code", how="left")
    merged["description"] = merged["description"].fillna("Produk tidak terdaftar")
    merged["category"] = merged["category"].fillna("Lainnya")
    return merged
