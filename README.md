# EventGuard

EventGuard adalah Sistem Peringatan Dini Cuaca (Early Warning System) khusus untuk Event Organizer (Penyelenggara Acara). Sistem ini membantu EO memantau kondisi cuaca secara proaktif di lokasi acara mereka untuk mencegah kerugian akibat cuaca ekstrem seperti hujan lebat, badai, atau suhu panas.

## Fitur Utama
1. **Dashboard Manajemen Acara:** Tambah, edit, hapus acara.
2. **Auto-Fetch Cuaca:** Penarikan otomatis ramalan cuaca (OpenWeatherMap) berdasarkan koordinat lokasi dan rentang waktu (interval 3 jam).
3. **Analisis Risiko (Risk Engine):** Penilaian otomatis Low, Medium, High Risk berdasarkan cuaca terburuk yang beririsan (*overlap*) dengan jadwal acara.
4. **Notifikasi:** Peringatan langsung (*Alert*) ketika status cuaca memburuk menjadi HIGH risk.
5. **Worker Berjalan di Latar Belakang:** Cron-job menggunakan APScheduler untuk mengecek perubahan cuaca setiap 6 jam.

## Prasyarat
- Python 3.10+
- Akun OpenWeatherMap (gratis) untuk API Key.

## Instalasi

1. **Clone repository ini:**
   ```bash
   git clone <repo_url>
   cd eventguard
   ```

2. **Buat Virtual Environment & Install Dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Di Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Atur Environment Variables:**
   ```bash
   cp .env.example .env.development
   ```
   Buka file `.env.development` dan isi `OPENWEATHER_API_KEY` milik Anda. Anda juga bisa menggunakan mode `OPENWEATHER_MODE=mock` untuk testing lokal tanpa API Key asli.

4. **Inisialisasi Database (Alembic):**
   ```bash
   alembic upgrade head
   ```

## Menjalankan Aplikasi

1. **Jalankan FastAPI Server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   Aplikasi akan berjalan di `http://127.0.0.1:8000`.

2. **Jalankan Background Worker (di terminal terpisah):**
   ```bash
   python worker/scheduler.py
   ```

3. **Gunakan CLI untuk Mengecek Cuaca Secara Cepat:**
   ```bash
   python cli/weather_cli.py check --city Jakarta
   ```

## Teknologi yang Digunakan
- **Backend:** FastAPI, Python
- **Database:** SQLite (Async) via SQLAlchemy & Alembic
- **Frontend:** Jinja2 Templates, TailwindCSS, Chart.js
- **Task Scheduler:** APScheduler
- **External API:** OpenWeatherMap API
