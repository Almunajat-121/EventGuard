# Handoff Document: EventGuard MVP (To Claude)

Halo Claude! Dokumen ini berisi rekap komprehensif mengenai status terakhir dari proyek **EventGuard** (aplikasi pemantau risiko cuaca untuk acara *outdoor*). Saya (Antigravity) baru saja menyelesaikan fase perbaikan bug krusial, pemantapan *backend*, penyelesaian *frontend* berdasarkan dokumen konsep, dan penyiapan berkas deployment.

Tolong jadikan dokumen ini sebagai acuan utama Anda (Context/Knowledge) sebelum melanjutkan penambahan fitur, perombakan arsitektur, atau pemecahan masalah (debugging) selanjutnya.

---

## 1. Status Proyek Secara Umum
Proyek saat ini **sudah layak disebut sebagai MVP awal** dan berfungsi penuh. 
- **Stack Utama:** FastAPI (Backend), SQLite (Database), SQLAlchemy Async + Alembic (ORM & Migrasi), Jinja2 (Templating Frontend), Typer (CLI), APScheduler (Background Worker), TailwindCSS (Styling CDN).
- **Authentication:** Menggunakan JWT yang disimpan dalam **HttpOnly Cookie** (bukan `localStorage`).
- **Mode Cuaca:** Saat ini beroperasi dengan `OPENWEATHER_MODE=mock` di lingkungan `.env.development` untuk simulasi respons OpenWeatherMap.

---

## 2. Ringkasan Perbaikan yang Telah Dilakukan (Backend)

*   **Penyatuan Logika Cuaca (Single Source of Truth):**
    Seluruh logika untuk _fetching_ cuaca dari OpenWeather, analisis risiko (_risk engine_), dan pengiriman notifikasi telah disatukan di `app/services/weather_updater.py`. *Routers* tidak lagi menangani logika operasional kompleks ini.
*   **Perbaikan Bug _Risk Engine_:**
    Menghapus kode _hack_ `or True` di `risk_engine.py` yang sebelumnya membuat aplikasi melewatkan evaluasi _threshold_ cuaca. Saat ini sistem memicu peringatan `HIGH` risk jika angin > 10m/s, peluang hujan > 50%, atau suhu ekstrem.
*   **Perbaikan Pemetaan *Field* Database:**
    Kolom `created_at` pada `WeatherLog` tidak lagi salah sasaran. _Timestamp_ untuk `fetched_at` dan `analyzed_at` sekarang disuntikkan secara tepat menggunakan `datetime.now(timezone.utc)` yang bersifat _timezone-aware_.
*   **Perbaikan Dashboard Query:**
    Memperbaiki endpoint `/api/dashboard/summary` agar secara akurat menghitung total acara (`total_events`) menggunakan fungsi `.distinct()` dari SQLAlchemy pada tabel `users_events` (bukan menghitung baris cuaca/log duplikat).
*   **Melengkapi API (CRUD & Weather):**
    Telah menyelesaikan sisa endpoint CRUD untuk `event_router.py` (Delete, Update) dan melengkapi `weather_router.py` (Historical Data, Risk Analysis Endpoint).

---

## 3. Ringkasan Perbaikan yang Telah Dilakukan (Frontend / UI)

Sesuai dengan `KONSEP_FE_EVENTGUARD.md` yang sebelumnya di-review oleh agen Codex, sisi _frontend_ telah dirombak secara ekstensif:

*   **Pembaruan Landing Page (`index.html`):** Telah ditambahkan bagian (section) *Hero*, *Features*, *Pricing* simulasi (SaaS model), dan *Contact Form*.
*   **Keamanan Sesi (*Session Integrity*):** Seluruh `fetch()` call di `dashboard.html` (termasuk API untuk Dashboard Summary, Events, Delete, Refresh Weather) sekarang menggunakan `credentials: 'include'` agar _cookie_ HttpOnly dapat menempel dengan valid ke API FastAPI.
*   **Penggantian `alert()` Menjadi Toast:** Menghapus penggunaan `alert()` yang memblokir _thread_ navigasi. Dibuatkan satu *container* Toast di `base.html` dengan _global function_ `showToast()` untuk _success, error_, dan _info state_.
*   **Dashboard Notifikasi Interaktif:** Menambahkan logo lonceng dengan *badge alert* yang memuat *dropdown* daftar notifikasi. Notifikasi ini secara otomatis mengecek (_auto-refresh_) *endpoint* `GET /api/notifications` setiap 30 detik. Fungsi "Tandai dibaca" juga sudah beroperasi.
*   **Visualisasi Chart.js:** Terpasang *Doughnut Chart* pada Dashboard yang memvisualisasikan rasio metrik antara acara berisiko Tinggi (High Risk) dibandingkan dengan acara berisiko Rendah/Sedang.
*   **Modal Detail Acara & Worst-Case Time:** Modal untuk mengeklik "Detail" acara sekarang menampakkan jam spesifik *Skenario Cuaca Terburuk* (_Worst Case Time_) beserta indikator parameter cuaca (Suhu, Peluang Hujan, Kecepatan Angin, dan Tingkat Risiko Keseluruhan).
*   **Tindakan Hapus Acara:** Menambahkan tautan UI "Hapus" pada _list_ acara beserta konfirmasi Javascript sebelum me-request metode `DELETE` ke backend.

---

## 4. Konfigurasi Deployment & Utilitas

*   **Typer CLI (`weather_cli.py`):** Modifikasi pada skrip utilitas CLI. Saat ini _fetching_ manual data cuaca kota bisa diakses secara rapi menggunakan _option flag_ bawaan Typer, contoh: `python cli/weather_cli.py check --city Jakarta`.
*   **Konfigurasi Nginx & Systemd:** Tersedia *folder* `deploy/` yang menyimpan konfigurasi `eventguard.service` dan `nginx.conf` siap pakai apabila EventGuard hendak dinaikkan (*deploy*) ke Virtual Private Server (VPS) produksi.
*   **Repository Hygiene:** Menyusun `.gitignore` yang tangguh dan membuat `README.md` dengan instruksi instalasi lokal (*Virtual Env*). Semua modifikasi saat ini sudah ter-*stage* siap di-*commit*.

---

## 5. Pesan Tambahan untuk Claude
Aplikasi ini menggunakan pola `SessionLocal` dari SQLAlchemy Async, dan manajemen _state_-nya cukup sensitif terhadap interupsi _Event Loop_ (`asyncio`). Apabila akan melakukan optimasi ke depannya, pastikan integrasi `APScheduler` (Background worker) tetap berjalan terpisah (atau di *thread/process* mandiri) agar tidak membuat _worker_ Uvicorn utamanya menjadi memblokir (blocking).

Terima kasih dan selamat melanjutkan estafet proyek ini!
*(Ditulis oleh Antigravity)*
