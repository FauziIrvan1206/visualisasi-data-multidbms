import os
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text
from db import get_database_url, init_postgres, init_sqlite, load_joined_data

st.set_page_config(page_title="Dashboard Retail Analytics", page_icon="📊", layout="wide")
st.title("📊 Dashboard Analisis Penjualan Retail")
st.caption("Proyek Visualisasi Data dan Informasi — integrasi PostgreSQL + SQLite dengan Pandas dan Plotly")

@st.cache_resource
def engines():
    url = get_database_url()
    pg = create_engine(url, pool_pre_ping=True) if url else None
    sqlite = create_engine("sqlite:///products.db", connect_args={"check_same_thread": False})
    init_sqlite(sqlite)
    if pg is not None:
        init_postgres(pg)
    return pg, sqlite

try:
    pg_engine, sqlite_engine = engines()
    if pg_engine is None:
        st.warning("Mode demo: DATABASE_URL belum diatur, jadi data transaksi dibaca dari SQLite demo. Untuk memenuhi syarat dua DBMS saat pengumpulan, siapkan PostgreSQL (misalnya Neon) dan atur DATABASE_URL di Secrets.")
        df = load_joined_data(None, sqlite_engine, demo=True)
    else:
        df = load_joined_data(pg_engine, sqlite_engine, demo=False)
except Exception as e:
    st.error("Aplikasi belum dapat membaca database. Periksa DATABASE_URL, tabel, dan langkah seed_data.py.")
    st.exception(e)
    st.stop()

if df.empty:
    st.info("Belum ada data. Jalankan `python seed_data.py` atau ikuti README untuk memuat dataset.")
    st.stop()

df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
df["revenue"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0) * pd.to_numeric(df["unit_price"], errors="coerce").fillna(0)
df = df.dropna(subset=["invoice_date"])
if "country" not in df.columns:
    df["country"] = "Tidak diketahui"

with st.sidebar:
    st.header("🔎 Filter Dashboard")
    min_date, max_date = df["invoice_date"].min().date(), df["invoice_date"].max().date()
    date_range = st.date_input("Rentang tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    categories = sorted(df["category"].fillna("Lainnya").unique().tolist())
    selected_categories = st.multiselect("Kategori produk", categories, default=categories)
    countries = sorted(df["country"].fillna("Tidak diketahui").unique().tolist())
    selected_countries = st.multiselect("Negara", countries, default=countries)
    st.caption("Gunakan filter untuk memperbarui seluruh visualisasi.")

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date
filtered = df[
    (df["invoice_date"].dt.date >= start_date) &
    (df["invoice_date"].dt.date <= end_date) &
    (df["category"].fillna("Lainnya").isin(selected_categories)) &
    (df["country"].fillna("Tidak diketahui").isin(selected_countries))
].copy()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Pendapatan", f"£{filtered['revenue'].sum():,.2f}")
c2.metric("Baris Transaksi", f"{len(filtered):,}")
c3.metric("Total Unit Terjual", f"{filtered['quantity'].sum():,.0f}")
c4.metric("Jumlah Negara", f"{filtered['country'].nunique():,}")

left, right = st.columns(2)
with left:
    monthly = filtered.assign(bulan=filtered["invoice_date"].dt.to_period("M").astype(str)).groupby("bulan", as_index=False)["revenue"].sum()
    st.subheader("Pendapatan per Bulan")
    if not monthly.empty:
        st.plotly_chart(px.line(monthly, x="bulan", y="revenue", markers=True, title="Tren pendapatan bulanan"), use_container_width=True)
    else:
        st.info("Tidak ada data untuk filter ini.")
with right:
    category_sales = filtered.groupby("category", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
    st.subheader("Pendapatan per Kategori")
    if not category_sales.empty:
        st.plotly_chart(px.bar(category_sales, x="category", y="revenue", title="Pendapatan berdasarkan kategori"), use_container_width=True)

st.subheader("Produk dengan Pendapatan Tertinggi")
top_products = filtered.groupby("description", as_index=False).agg(pendapatan=("revenue", "sum"), unit=("quantity", "sum")).sort_values("pendapatan", ascending=False).head(10)
if not top_products.empty:
    st.plotly_chart(px.bar(top_products.sort_values("pendapatan"), x="pendapatan", y="description", orientation="h", title="10 produk teratas"), use_container_width=True)

st.subheader("Pratinjau Data Terintegrasi")
st.caption(f"Menampilkan {min(500, len(filtered)):,} baris pertama setelah filter.")
st.dataframe(filtered[["invoice_no", "invoice_date", "stock_code", "description", "category", "quantity", "unit_price", "revenue", "country"]].head(500), use_container_width=True, hide_index=True)
st.download_button("⬇️ Unduh data hasil filter (CSV)", data=filtered.to_csv(index=False).encode("utf-8"), file_name="hasil_analisis_penjualan.csv", mime="text/csv")

with st.expander("Tentang proyek dan arsitektur"):
    st.markdown("""
    - **PostgreSQL**: menyimpan data transaksi retail (fakta transaksi).
    - **SQLite**: menyimpan referensi produk dan kategori.
    - **Pandas**: menggabungkan data transaksi dengan referensi produk menggunakan `merge()`.
    - **Plotly + Streamlit**: grafik dan filter interaktif.
    - Dataset utama: UCI Online Retail. Pendapatan dihitung sebagai `Quantity × UnitPrice`.
    - Catatan: transaksi pembatalan dan kuantitas negatif tidak otomatis dihapus agar proses pembersihan dapat dijelaskan; interpretasikan hasil dengan memperhatikan karakter dataset.
    """)
