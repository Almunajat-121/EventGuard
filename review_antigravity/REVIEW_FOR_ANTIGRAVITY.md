# Review EventGuard untuk Antigravity

Dokumen ini berisi hasil review kode EventGuard terhadap `konsep.md` dan `konsep_updated.md`.
Peran reviewer: memeriksa apakah implementasi Antigravity sudah sesuai konsep, menemukan bug, dan memberi arahan perbaikan.

## Ringkasan

Project EventGuard sudah cukup dekat dengan `konsep_updated.md` pada level struktur dan fondasi:

- FastAPI sudah menjadi entrypoint aplikasi.
- SQLAlchemy async sudah dipakai.
- Model utama sudah tersedia: `User`, `Event`, `WeatherLog`, `RiskAnalysis`, dan `Notification`.
- Auth sudah menggunakan JWT di HttpOnly cookie.
- Router utama sudah ada: auth, event, weather, dashboard, notification, landing.
- Service OpenWeather, risk engine, recommendation engine, CLI, dan worker scheduler sudah tersedia.
- `.env.development` dan mode mock OpenWeather sudah tersedia.

Namun implementasi belum sepenuhnya sesuai konsep final. Ada beberapa bug yang perlu diperbaiki sebelum aplikasi dianggap siap untuk demo/presentasi.

## Prioritas Perbaikan Tinggi

### 1. Bug pada endpoint detail event

File: `app/routers/event_router.py`

Endpoint `/api/events/{event_id}/details` mengurutkan data memakai atribut yang tidak ada:

```python
WeatherLog.created_at
RiskAnalysis.created_at
```

Padahal model memakai:

```python
WeatherLog.fetched_at
RiskAnalysis.analyzed_at
```

Perbaikan:

```python
.order_by(WeatherLog.fetched_at.desc())
```

dan:

```python
.order_by(RiskAnalysis.analyzed_at.desc())
```

Jika tidak diperbaiki, modal detail event di dashboard kemungkinan gagal mengambil data.

### 2. Worst-case scenario belum sesuai konsep

File: `app/services/risk_engine.py`

Saat ini ada kondisi:

```python
if item_time >= event_start or item_time <= event_end or True:
```

Karena ada `or True`, semua forecast pada tanggal event akan selalu dihitung, bukan hanya forecast yang overlap dengan jam acara.

Ini bertentangan dengan `konsep_updated.md`, yang meminta sistem mengambil data forecast interval 3 jam yang bersinggungan dengan rentang `[start_time, end_time]`.

Perbaikan yang disarankan:

- Hapus `or True`.
- Buat logika overlap interval forecast 3 jam dengan rentang waktu event.
- Untuk event multi-hari, pertimbangkan `start_date` sampai `end_date`, bukan hanya satu tanggal.

### 3. Create event belum melakukan initial weather fetch

File: `app/routers/event_router.py`

Saat membuat event, masih ada TODO:

```python
# TODO: Panggil BackgroundTasks untuk initial fetch cuaca jika AVAILABLE
```

Konsep awal dan konsep final menyebutkan bahwa create event seharusnya dapat memicu fetch cuaca dan analisis risiko jika forecast tersedia.

Perbaikan:

- Gunakan `BackgroundTasks`, atau
- Panggil fungsi refresh weather/risk reusable setelah event tersimpan, jika `forecast_status == "AVAILABLE"`.

### 4. Notifikasi HIGH risk bisa spam atau tidak muncul sesuai konsep

File: `app/routers/weather_router.py`

Saat manual refresh, setiap hasil `overall_risk == "HIGH"` langsung membuat notifikasi baru. Ini bisa membuat spam.

File: `worker/scheduler.py`

Worker menambahkan `RiskAnalysis` baru sebelum mencari previous risk. Akibatnya previous risk yang terbaca bisa jadi risk yang baru saja dibuat, bukan risk sebelumnya.

Perbaikan:

- Ambil latest previous risk sebelum insert risk baru.
- Buat notifikasi hanya jika previous risk bukan `HIGH` dan risk baru menjadi `HIGH`.
- Gunakan logika yang sama untuk manual refresh dan scheduler.

## Prioritas Perbaikan Sedang

### 5. Endpoint API belum lengkap

Konsep menyebutkan endpoint berikut, tetapi implementasi belum lengkap:

- `GET /api/events/{id}`
- `PUT /api/events/{id}`
- `DELETE /api/events/{id}`
- `GET /api/events/{id}/weather`
- `GET /api/events/{id}/weather/history`
- `GET /api/events/{id}/risk`
- `POST /api/events/{id}/risk/analyze`

Saat ini project lebih berbentuk MVP dashboard dengan endpoint custom `/details` dan `/weather/refresh`.

### 6. Dashboard summary high risk bisa menghitung dobel

File: `app/routers/dashboard_router.py`

Query high risk menghitung semua baris `risk_analysis` dengan `overall_risk == "HIGH"`.
Jika satu event memiliki beberapa log HIGH, event tersebut bisa terhitung lebih dari sekali.

Perbaikan:

- Hitung berdasarkan risk terbaru per event.
- Atau gunakan `distinct(Event.id)` sebagai perbaikan MVP.

### 7. Humidity dan cloud coverage belum diambil dari data asli

File: `app/services/risk_engine.py`

Saat ini:

```python
"humidity": 0.0
"cloud_coverage": 0.0
```

Padahal data tersedia dari OpenWeather/mock:

```python
item["main"]["humidity"]
item["clouds"]["all"]
```

Perbaikan:

- Ambil nilai worst-case atau nilai pada waktu worst rain.
- Simpan hasil mapping ke `weather_logs`.

### 8. Landing page belum lengkap

File: `app/templates/index.html`

Landing page saat ini baru memiliki hero section. Konsep meminta 4 section:

- Hero
- Features
- Pricing
- Contact

Perbaikan:

- Tambahkan section features 4-6 item.
- Tambahkan pricing Free/Pro/Enterprise.
- Tambahkan contact form simulasi.

### 9. Dashboard belum benar-benar memakai Chart.js

File: `app/templates/base.html` sudah memuat Chart.js, tetapi `dashboard.html` belum membuat chart.

Konsep final menyebut Dashboard Interaktif dengan Fetch API dan Chart.js.

Perbaikan:

- Tambahkan chart ringkas, misalnya distribusi risiko LOW/MEDIUM/HIGH atau summary event.

### 10. Fetch API belum eksplisit memakai credentials include

File: `app/templates/dashboard.html`

Karena auth memakai HttpOnly cookie, konsep final menyebutkan fetch API sebaiknya:

```javascript
credentials: "include"
```

Untuk same-origin biasanya cookie tetap terkirim, tetapi lebih baik dibuat eksplisit agar sesuai konsep.

## Prioritas Perbaikan Rendah

### 11. `.env.production` dan file deployment belum tersedia

Konsep menyebut:

- `.env.production`
- folder `deploy/`
- systemd service API
- systemd service worker
- nginx config

File-file ini belum terlihat di project.

Perbaikan:

- Tambahkan template deployment tanpa secret asli.
- Tambahkan README singkat cara menjalankan development dan production.

### 12. CLI belum persis sesuai command konsep

Konsep mengharapkan:

```bash
weather-cli --city Kendari
```

Implementasi Typer saat ini kemungkinan lebih natural dipanggil sebagai:

```bash
python cli/weather_cli.py check Kendari
```

Perbaikan:

- Tambahkan packaging entry point, atau
- Sesuaikan command Typer agar bisa menerima opsi `--city`.

## Catatan Positif

- Pemilihan async SQLAlchemy sudah sesuai konsep final.
- Model database sudah lebih maju daripada konsep awal karena sudah mendukung notification dan event multi-hari.
- Worker APScheduler sudah dibuat sebagai service terpisah, sesuai `konsep_updated.md`.
- Auth HttpOnly cookie sudah cocok untuk Jinja2 SSR.
- Service OpenWeather sudah mendukung mock/live mode.
- Risk dan recommendation engine sudah dipisah, sehingga mudah dirapikan.

## Rekomendasi Urutan Kerja

1. Perbaiki bug `created_at` pada endpoint detail event.
2. Perbaiki logika worst-case overlap di `risk_engine.py`.
3. Buat fungsi reusable untuk refresh weather + risk + notification agar tidak duplikasi antara router dan worker.
4. Perbaiki notifikasi agar hanya muncul saat eskalasi ke HIGH.
5. Tambahkan initial fetch saat create event jika forecast tersedia.
6. Lengkapi endpoint CRUD event, weather history, dan risk analyze.
7. Lengkapi landing page sesuai konsep.
8. Tambahkan Chart.js sederhana di dashboard.
9. Tambahkan file deployment dan `.env.production.example`.
10. Rapikan CLI agar sesuai format command di konsep.

## Kesimpulan Reviewer

Project ini sudah layak disebut MVP awal EventGuard, tetapi belum sepenuhnya sesuai `konsep_updated.md`.
Bagian yang paling perlu diperbaiki adalah logika worst-case forecast, endpoint detail yang memakai field salah, dan notifikasi HIGH risk.

Jika targetnya presentasi atau demo, minimal perbaiki prioritas tinggi terlebih dahulu agar flow register, login, create event, refresh weather, lihat detail risk, dan notifikasi berjalan stabil.
