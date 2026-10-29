"""Muat data ke SQLite (referensi produk) dan PostgreSQL (transaksi).
Dataset asli: UCI Online Retail, file Excel Online Retail.xlsx.
Jika file belum tersedia, skrip tetap mengisi SQLite produk demo; unduh dataset untuk memuat transaksi asli.
"""
from pathlib import Path
import re
import pandas as pd
from sqlalchemy import create_engine, text
from db import get_database_url, init_sqlite, init_postgres

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

def category_for(description):
    d = str(description).upper()
    rules = [
        ("Dekorasi", ["CANDLE", "DECORATION", "FRAME", "ORNAMENT", "HOLDER"]),
        ("Dapur", ["MUG", "CUP", "PLATE", "BOWL", "KITCHEN", "TEA", "COFFEE"]),
        ("Aksesori", ["NECKLACE", "BRACELET", "EARRING", "RING", "BAG", "PURSE"]),
        ("Alat Tulis", ["PEN", "PENCIL", "NOTEBOOK", "PAPER", "CARD"]),
        ("Mainan", ["TOY", "GAME", "DOLL", "PUZZLE"]),
        ("Tekstil", ["CUSHION", "COVER", "TOWEL", "FABRIC", "BLANKET"]),
    ]
    for category, keywords in rules:
        if any(k in d for k in keywords):
            return category
    return "Lainnya"

def main():
    sqlite_engine = create_engine("sqlite:///products.db")
    init_sqlite(sqlite_engine)
    xlsx = DATA / "Online Retail.xlsx"
    if xlsx.exists():
        raw = pd.read_excel(xlsx)
        raw = raw.rename(columns={
            "InvoiceNo":"invoice_no", "StockCode":"stock_code", "Description":"description",
            "Quantity":"quantity", "InvoiceDate":"invoice_date", "UnitPrice":"unit_price",
            "CustomerID":"customer_id", "Country":"country"
        })
        raw["stock_code"] = raw["stock_code"].astype(str)
        raw["customer_id"] = raw["customer_id"].astype("string")
        products = raw[["stock_code", "description"]].dropna(subset=["stock_code"]).drop_duplicates("stock_code").copy()
        products["category"] = products["description"].apply(category_for)
        products.to_sql("products", sqlite_engine, if_exists="replace", index=False)
        url = get_database_url()
        if not url:
            print("Produk dari dataset asli telah dimuat ke SQLite.")
            print("DATABASE_URL belum ada, jadi transaksi belum dimuat ke PostgreSQL.")
            print("Atur DATABASE_URL di environment atau .streamlit/secrets.toml, lalu jalankan ulang.")
            return
        pg_engine = create_engine(url, pool_pre_ping=True)
        init_postgres(pg_engine)
        tx = raw[["invoice_no","stock_code","quantity","invoice_date","unit_price","customer_id","country"]].copy()
        tx["invoice_no"] = tx["invoice_no"].astype(str)
        tx["stock_code"] = tx["stock_code"].astype(str)
        tx["customer_id"] = tx["customer_id"].astype("string").fillna("")
        tx = tx.dropna(subset=["invoice_no","stock_code","quantity","invoice_date","unit_price"])
        with pg_engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE transactions"))
        tx.to_sql("transactions", pg_engine, if_exists="append", index=False, chunksize=5000, method="multi")
        print(f"Berhasil memuat {len(products):,} produk ke SQLite dan {len(tx):,} baris transaksi ke PostgreSQL.")
    else:
        sample = pd.read_csv(DATA / "sample_transactions.csv")
        products = sample[["stock_code","description"]].drop_duplicates("stock_code").copy()
        products["category"] = products["description"].apply(category_for)
        products.to_sql("products", sqlite_engine, if_exists="replace", index=False)
        print("Data demo dimuat ke SQLite. Untuk data asli, unduh file 'Online Retail.xlsx' dari UCI dan simpan ke folder data/.")
        print("Untuk memenuhi syarat multi-DBMS, atur DATABASE_URL dan jalankan skrip lagi.")
if __name__ == "__main__":
    main()
