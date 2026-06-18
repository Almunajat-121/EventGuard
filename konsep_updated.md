# KONSEP APLIKASI LENGKAP: EVENTGUARD (FINAL)

## 1. OVERVIEW PROYEK

**Nama Aplikasi:** EventGuard
**Kategori:** SaaS (Software as a Service)
**Domain Masalah:** Weather risk monitoring untuk event outdoor

EventGuard adalah platform SaaS yang membantu penyelenggara acara outdoor (event organizer, wedding organizer, panitia kampus, komunitas olahraga, penyelenggara konser/festival) untuk memantau risiko cuaca terhadap acara mereka dan mendapatkan rekomendasi tindakan sebelum acara berlangsung. Aplikasi ini bukan sekadar menampilkan prakiraan cuaca seperti aplikasi cuaca umum, tetapi mengubah data cuaca mentah menjadi penilaian risiko terstruktur (LOW/MEDIUM/HIGH) dan rekomendasi actionable per event yang dibuat pengguna.

**Mengapa ini SaaS:** Setiap pengguna memiliki akun sendiri, dapat membuat banyak event, data tersimpan persisten di database, sistem melakukan monitoring otomatis berkelanjutan, dan terdapat model pricing bertingkat (Free/Pro/Enterprise) yang membatasi kuota berdasarkan subscription tier.

**Problem Statement:**
Penyelenggara acara saat ini hanya mengandalkan aplikasi cuaca umum yang tidak memiliki: monitoring khusus per event, sistem penilaian risiko otomatis, notifikasi proaktif, dashboard pengelolaan multi-event, dan rekomendasi tindakan kontekstual.

---

## 2. TARGET PENGGUNA

- Event Organizer (EO) profesional
- Wedding Organizer
- Panitia kampus (BEM, himpunan mahasiswa, panitia ospek/dies natalis)
- Komunitas olahraga (lari, sepeda, hiking)
- Promotor konser dan festival musik
- Organisasi/perusahaan yang rutin mengadakan kegiatan luar ruangan

---

## 3. ARSITEKTUR SISTEM

### 3.1 Tech Stack

```text
Backend     : Python 3.12 + FastAPI (menggunakan driver async untuk database)
ORM         : SQLAlchemy 2.x (Async) + Alembic (migration)
Database    : PostgreSQL 16 (production), SQLite (opsional untuk dev cepat)
Validation  : Pydantic v2
Auth        : JWT disimpan dalam HttpOnly Cookie (Aman dari XSS, mendukung Jinja2 SSR)
Frontend    : Hybrid -> Jinja2 (untuk Landing Page & Auth) + Fetch API & Chart.js (untuk Dashboard Interaktif)
CLI Tool    : Typer (Python CLI framework)
Task runner : APScheduler (Berjalan sebagai worker/service terpisah untuk monitoring berkala) & FastAPI BackgroundTasks (untuk task sekali jalan)
Web Server  : Gunicorn + Uvicorn worker (ASGI) di-reverse-proxy oleh Nginx
Process mgr : systemd service
HTTPS       : Certbot (Let's Encrypt)
External API: OpenWeatherMap API (Current Weather, 5-Day Forecast, Geocoding)
```

### 3.2 Arsitektur Layer

```text
[Browser/Client]
      |
      v
[Nginx :80/:443] --(reverse proxy)--> [Gunicorn+Uvicorn :8000 (API & Web)]
      |                                         |
      | (static files /static, /media)          v
      |                                  [FastAPI Application]
      |                                   |-- Auth Module (HttpOnly Cookie)
      |                                   |-- Event Management Module
      |                                   |-- Weather Monitoring Module --> [OpenWeatherMap API]
      |                                   |-- Risk Analysis Engine
      |                                   |-- Recommendation Engine
      |                                   |-- Notification Module
      |                                   |-- Dashboard/Reporting Module
      |                                         |
      |                                         v
      |                                  [PostgreSQL Database]
      |                                         ^
      |                                         |
[APScheduler Worker] --(polling berkala)--------+
      |
[CLI Tool: weather-cli] -- (jalan terpisah di server) --> [OpenWeatherMap API]
```

### 3.3 Folder Structure (rekomendasi)

```text
eventguard/
├── app/
│   ├── main.py                  # entrypoint FastAPI
│   ├── config.py                # load env vars (Pydantic Settings)
│   ├── database.py              # SQLAlchemy engine/session (Async)
│   ├── models/
│   │   ├── user.py
│   │   ├── event.py
│   │   ├── weather_log.py
│   │   ├── risk_analysis.py
│   │   └── notification.py
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── routers/                 # API & HTML Routes
│   ├── services/
│   │   ├── openweather_service.py
│   │   ├── risk_engine.py
│   │   └── recommendation_engine.py
│   ├── core/
│   │   ├── security.py          # JWT, Cookie handling
│   │   └── deps.py              # dependency injection (get_current_user_from_cookie)
│   └── templates/               # Jinja2 HTML (landing, dashboard shell, login)
├── worker/
│   └── scheduler.py             # Script terpisah untuk APScheduler (monitoring berkala)
├── cli/
│   └── weather_cli.py           # Typer CLI standalone
├── alembic/                     # migration scripts
├── .env.development
├── .env.production
├── requirements.txt
└── deploy/
    ├── eventguard-api.service
    ├── eventguard-worker.service
    └── nginx_eventguard.conf
```

---

## 4. SKEMA DATABASE (DETAIL)

**Penting:** Semua waktu (TIMESTAMP) harus disimpan dalam format UTC.

### Tabel: users
| Kolom | Tipe | Constraint |
|---|---|---|
| id | UUID / SERIAL | PRIMARY KEY |
| name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(150) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| subscription_tier | VARCHAR(20) | DEFAULT 'free' |
| created_at | TIMESTAMP (UTC) | DEFAULT now() |

### Tabel: events
| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| id | UUID / SERIAL | PRIMARY KEY | |
| user_id | FK -> users.id | NOT NULL | |
| name | VARCHAR(150) | NOT NULL | |
| location | VARCHAR(200) | NOT NULL | |
| latitude | FLOAT | nullable | hasil geocoding |
| longitude | FLOAT | nullable | hasil geocoding |
| timezone | VARCHAR(50) | NOT NULL | contoh: 'Asia/Jakarta' |
| start_date | DATE | NOT NULL | Dukungan multi-hari |
| end_date | DATE | NOT NULL | Dukungan multi-hari |
| start_time | TIME | NOT NULL | |
| end_time | TIME | NOT NULL | |
| forecast_status | VARCHAR(20) | DEFAULT 'TOO_FAR' | TOO_FAR / AVAILABLE / PASSED |
| status | VARCHAR(20) | DEFAULT 'upcoming' | upcoming/active/done |
| created_at | TIMESTAMP (UTC) | DEFAULT now() | |

### Tabel: weather_logs
| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| id | UUID / SERIAL | PRIMARY KEY | |
| event_id | FK -> events.id | NOT NULL | |
| temperature | FLOAT | | Nilai *worst-case* |
| humidity | FLOAT | | Nilai *worst-case* |
| wind_speed | FLOAT | | Nilai *worst-case* |
| cloud_coverage | FLOAT | | Nilai *worst-case* |
| rain_probability | FLOAT | | Nilai *worst-case* |
| worst_case_time | TIME | nullable | Waktu terjadinya cuaca terburuk |
| source_env | VARCHAR(20) | 'live'/'mock' | |
| fetched_at | TIMESTAMP (UTC) | DEFAULT now() | |

### Tabel: risk_analysis
*(Bersifat Log Historis, selalu INSERT, bukan UPDATE)*

| Kolom | Tipe | Constraint |
|---|---|---|
| id | UUID / SERIAL | PRIMARY KEY |
| event_id | FK -> events.id | NOT NULL |
| rain_risk | VARCHAR(10) | LOW/MEDIUM/HIGH/PENDING |
| wind_risk | VARCHAR(10) | LOW/MEDIUM/HIGH/PENDING |
| heat_risk | VARCHAR(10) | LOW/MEDIUM/HIGH/PENDING |
| overall_risk | VARCHAR(10) | LOW/MEDIUM/HIGH/PENDING |
| recommendation | TEXT | |
| analyzed_at | TIMESTAMP (UTC) | DEFAULT now() |

### Tabel: notifications (Notifikasi In-App)
| Kolom | Tipe | Constraint |
|---|---|---|
| id | UUID / SERIAL | PRIMARY KEY |
| user_id | FK -> users.id | NOT NULL |
| event_id | FK -> events.id | nullable |
| type | VARCHAR(50) | cth: 'RISK_ALERT' |
| message | TEXT | NOT NULL |
| is_read | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMP (UTC) | DEFAULT now() |

---

## 5. DAFTAR ENDPOINT API

**Auth (Menggunakan HttpOnly Cookie dengan SameSite=Lax):**
```
POST   /api/auth/register
POST   /api/auth/login         -> Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Lax
POST   /api/auth/logout        -> Clear-Cookie: access_token
```

**Notifications:**
```
GET    /api/notifications            -> List notifikasi (filter unread)
PATCH  /api/notifications/{id}/read  -> Tandai sudah dibaca
```

*(Endpoint Events, Weather, Risk, dan Dashboard sama seperti konsep sebelumnya)*

---

## 6. LOGIKA BISNIS

### 6.1 Weather Monitoring Flow & Worst-Case Scenario
1. API Forecast 5-Hari mengembalikan data dalam interval 3-jam.
2. Saat mengolah response OpenWeatherMap, sistem mencari semua *data point* (interval 3-jam) yang *overlap* (bersinggungan) dengan rentang `[start_time, end_time]` acara pada hari tersebut.
3. Untuk setiap metrik cuaca (misal probabilitas hujan), sistem mengambil nilai **Maksimum (Terburuk/Worst-Case)** dari seluruh interval yang overlap, BUKAN nilai rata-ratanya.
4. Nilai terburuk ini yang disimpan ke `weather_logs`, beserta jam kejadiannya (`worst_case_time`).
5. Ini memastikan EO diinformasikan tentang risiko puncak selama acara berlangsung, meskipun ada waktu lain yang cerah di dalam rentang acara tersebut.

### 6.2 Notifikasi Proaktif (In-App)
- Saat `APScheduler` berjalan (misal setiap 6 jam) dan menghitung ulang `Risk Analysis`:
- Jika status `overall_risk` acara berubah menjadi `HIGH` (dibandingkan dengan *log* analisis sebelumnya), maka trigger `INSERT` ke tabel `notifications`.
- Jangan melakukan *spam* jika risiko sudah `HIGH` dari siklus sebelumnya dan masih `HIGH`. Notifikasi dibuat hanya saat ada eskalasi ke `HIGH` atau jika ada perubahan signifikan yang perlu diberitahukan.

---

## 7. MULTI-ENVIRONMENT STRATEGY
*(Sama seperti konsep awal)*

---

## 8. CLI TOOL
*(Sama seperti konsep awal)*

---

## 9. LANDING PAGE SAAS & DASHBOARD INTERAKTIF
- **Auth Flow:** Karena JWT disimpan di **HttpOnly Cookie**, server FastAPI dapat langsung mengenali user saat merender template Jinja2 via `Depends(get_current_user_from_cookie)`. Ini menghilangkan efek "*flash of unauthenticated content*" yang terjadi jika menggunakan `localStorage`.
- **Dashboard API:** JavaScript `fetch()` di frontend (untuk memperbarui Chart.js) wajib menyertakan `credentials: "include"` agar Cookie dikirim ke API backend dalam satu origin yang sama.

---

## 10. DEPLOYMENT FLOW
*(Sama seperti konsep sebelumnya: 2 Systemd Services terpisah untuk API dan Worker Scheduler).*
