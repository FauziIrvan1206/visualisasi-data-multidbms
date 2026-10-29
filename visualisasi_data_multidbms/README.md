# Dashboard Analisis Penjualan Retail — Multi-DBMS

Proyek tugas Visualisasi Data dan Informasi: pipeline data dengan PostgreSQL + SQLite, integrasi Pandas, dan dashboard Streamlit/Plotly.

## 1. Arsitektur
- **PostgreSQL** menyimpan transaksi (`transactions`): nomor faktur, kode produk, jumlah, tanggal, harga satuan, pelanggan, dan negara.
- **SQLite** menyimpan referensi produk (`products`): kode produk, deskripsi, dan kategori.
- **Pandas** menggabungkan keduanya dengan `merge(..., on="stock_code", how="left")`.
- **Streamlit + Plotly** menyajikan KPI, tren bulanan, pendapatan per kategori, produk teratas, filter, dan unduhan CSV.

```text
UCI Online Retail (Excel)
       |                         |
       v                         v
PostgreSQL: transactions     SQLite: products
       \                         /
        \---- SQLAlchemy -------/
                    |
               Pandas merge()
                    |
             Streamlit + Plotly
                    |
             Dashboard web publik
```

## 2. Sumber data dan referensi
- Dataset primer: UCI Machine Learning Repository, **Online Retail**: https://archive.ics.uci.edu/dataset/352/online+retail
- Dokumentasi deployment Streamlit Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
- Dokumentasi secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Contoh repositori teknik dashboard Streamlit: https://github.com/prathamgarg1603-ml/Streamlit-Interactive-Dashboard
- Kode pada proyek ini ditulis untuk tugas ini; repositori contoh di atas digunakan sebagai referensi pendekatan dashboard, bukan untuk mengklaim kepemilikan kode pihak lain.

Dataset UCI adalah data transaksi retail Inggris pada 2010–2011. Pendapatan dihitung sebagai `quantity × unit_price`. Kolom `StockCode` dipakai sebagai kunci integrasi. Kategori produk dibuat dengan aturan kata kunci sederhana dari deskripsi, sehingga kategori adalah klasifikasi buatan proyek, bukan kategori resmi dataset.

## 3. Jalankan lokal (pemula)
### A. Persiapan
1. Instal Python 3.11 atau 3.12 dari https://www.python.org/downloads/ (Windows: centang **Add Python to PATH**).
2. Ekstrak ZIP proyek.
3. Buka folder proyek di VS Code, atau buka Command Prompt lalu masuk ke folder proyek.
4. Buat virtual environment:
   - Windows: `py -m venv .venv`
   - Aktifkan: `.venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv .venv`, lalu `source .venv/bin/activate`
5. Instal pustaka: `pip install -r requirements.txt`

### B. Unduh dataset asli
1. Buka https://archive.ics.uci.edu/dataset/352/online+retail
2. Unduh file **Online Retail.xlsx**.
3. Letakkan file tersebut di folder `data/` (sejajar dengan `sample_transactions.csv`).

### C. Siapkan PostgreSQL
Untuk memenuhi syarat dua DBMS, buat database PostgreSQL di layanan yang mendukung koneksi PostgreSQL (misalnya Neon) atau di komputer sendiri. Salin connection string database. Format umum:
`postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require`
Jangan unggah password ke GitHub.

Buat file `.streamlit/secrets.toml` secara lokal (file ini masuk `.gitignore`):
```toml
[postgres]
url = "postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require"
```
Ganti URL contoh dengan connection string milikmu. Jangan mengirimkan password ke orang lain.

### D. Isi database
Di terminal yang masih berada di folder proyek dan virtual environment aktif, jalankan:
`python seed_data.py`

Jika file Excel ditemukan dan `DATABASE_URL`/Secrets telah diatur, skrip akan mengisi tabel transaksi PostgreSQL dan tabel produk SQLite. Untuk memastikan environment lokal terbaca, kamu juga dapat mengatur variabel `DATABASE_URL` sebelum menjalankan skrip:
- PowerShell: `$env:DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require"`
- macOS/Linux: `export DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require"`

### E. Jalankan dashboard
`streamlit run app.py`
Browser akan membuka dashboard lokal. Jika PostgreSQL belum dikonfigurasi, aplikasi memakai data demo lokal; mode ini hanya untuk mencoba UI dan belum memenuhi syarat multi-DBMS.

## 4. Deploy publik ke Streamlit Community Cloud
1. Buat akun GitHub dan repositori **public** baru.
2. Unggah semua file proyek, tetapi **jangan** unggah `secrets.toml`, file Excel, atau password.
3. Buka https://share.streamlit.io/ lalu masuk dengan GitHub.
4. Klik **Create app**, pilih repositori, branch `main`, dan file `app.py`.
5. Pada **Advanced settings / Secrets**, masukkan:
```toml
[postgres]
url = "postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require"
```
6. Deploy, tunggu sampai selesai, lalu buka URL `*.streamlit.app`.
7. Penting: SQLite di hosting dapat bersifat sementara; aplikasi ini menggunakan SQLite untuk tabel referensi produk. Untuk penggunaan publik yang stabil, pastikan tabel produk tersedia saat deployment. Cara termudah: seed `products.db` sebelum push hanya jika dataset kecil dan diizinkan, atau ubah tabel referensi menjadi PostgreSQL juga jika dosen menyetujui interpretasi arsitektur. Jangan pernah mengunggah data pribadi atau rahasia.

## 5. Struktur proyek
```text
visualisasi_data_multidbms/
├── app.py
├── db.py
├── seed_data.py
├── requirements.txt
├── README.md
├── products.db                 # dibuat lokal, tidak di-commit secara default
├── data/
│   └── sample_transactions.csv  # data demo buatan, bukan dataset UCI
├── sql/
│   └── schema_postgres.sql
└── .streamlit/
    └── config.toml
```

## 6. Fitur aplikasi
- KPI: total pendapatan, baris transaksi, unit terjual, jumlah negara.
- Filter rentang tanggal, kategori, dan negara.
- Grafik tren pendapatan per bulan.
- Grafik pendapatan berdasarkan kategori.
- Grafik 10 produk teratas.
- Pratinjau data gabungan dan ekspor CSV.
- Pipeline multi-DBMS melalui SQLAlchemy dan Pandas.

## 7. Batasan dan hal yang perlu diverifikasi sebelum dikumpulkan
- `sample_transactions.csv` hanya data demo untuk mengetes tampilan; jangan menyebutnya data asli.
- Koneksi PostgreSQL, seed dataset UCI, dan deployment harus diuji menggunakan akun/layanan milik mahasiswa.
- Kategori produk dibuat dengan pencocokan kata kunci sederhana.
- Sebelum mengumpulkan, buka URL publik di jendela incognito dan pastikan dashboard benar-benar dapat diakses.
- Lengkapi identitas (nama/NIM) dan tautan live app, GitHub, dataset, dan referensi kode pada form LMS sesuai instruksi dosen.



## Arsitektur Sistem

Proyek ini mengintegrasikan dua DBMS menggunakan Python untuk mendukung analisis data transaksi ritel.

### 1. Database yang Digunakan

- **DBMS 1 — SQLite:** Menggunakan engine SQLite melalui SQLAlchemy. Menyimpan data produk pada tabel `products`, termasuk kode produk, deskripsi, dan kategori.
- **DBMS 2 — PostgreSQL:** Menggunakan engine PostgreSQL melalui SQLAlchemy. Database di-host menggunakan Neon dan menyimpan data transaksi pada tabel `transactions`.

### 2. Diagram Arsitektur

```text
Data Produk
    |
    v
SQLite (products.db)
    |
    |                     Data Transaksi
    |                          |
    |                          v
    |                 PostgreSQL (Neon)
    |                          |
    +------------+-------------+
                 |
                 v
          Python + SQLAlchemy
                 |
                 v
              Pandas
    Membaca dan menggabungkan data
       berdasarkan kode produk
                 |
                 v
        Streamlit + Plotly
                 |
                 v
       Dashboard Visualisasi Web
```

### 3. Alur Data Pipeline

1. Python membuat koneksi ke SQLite dan PostgreSQL menggunakan SQLAlchemy.
2. Data produk dibaca dari tabel `products` di SQLite.
3. Data transaksi dibaca dari tabel `transactions` di PostgreSQL.
4. Pandas mengolah data dan menggabungkan transaksi dengan informasi produk berdasarkan `stock_code`.
5. Data hasil integrasi digunakan untuk menghitung ringkasan dan membuat visualisasi.
6. Streamlit menampilkan dashboard dan Plotly menyajikan grafik interaktif.

### 4. Fitur Dashboard

- Ringkasan data transaksi.
- Grafik visualisasi transaksi dan penjualan.
- Filter interaktif untuk mengeksplorasi data.
- Penggabungan data produk dan transaksi dari dua DBMS.
- Dashboard web yang dapat diakses secara publik.

### 5. Teknologi

Python, SQLite, PostgreSQL, Neon, SQLAlchemy,
Pandas, Streamlit, dan Plotly.

### 6. Validasi Database

Tabel `transactions` pada PostgreSQL telah diperiksa menggunakan query `COUNT(*)` dan menghasilkan 50 baris data pada saat verifikasi.
