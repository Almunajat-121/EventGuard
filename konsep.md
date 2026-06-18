# KONSEP APLIKASI LENGKAP: EVENTGUARD

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

```
Backend     : Python 3.12 + FastAPI
ORM         : SQLAlchemy 2.x + Alembic (migration)
Database    : PostgreSQL 16 (production), SQLite (opsional untuk dev cepat)
Validation  : Pydantic v2
Auth        : JWT (access token) + bcrypt (password hashing)
Frontend    : Jinja2 server-rendered templates + TailwindCSS (CDN) + vanilla JS
             (alternatif: pisahkan jadi React SPA jika tim familiar React)
CLI Tool    : Typer (Python CLI framework)
Task runner : APScheduler (untuk monitoring cuaca berkala) — opsional, bisa manual trigger
Web Server  : Gunicorn + Uvicorn worker (ASGI) di-reverse-proxy oleh Nginx
Process mgr : systemd service
HTTPS       : Certbot (Let's Encrypt)
Container   : Docker + Docker Compose (opsional, nilai tambah)
External API: OpenWeatherMap API (Current Weather, 5-Day Forecast, Geocoding)
```

### 3.2 Arsitektur Layer

```
[Browser/Client]
      |
      v
[Nginx :80/:443] --(reverse proxy)--> [Gunicorn+Uvicorn :8000 (internal)]
      |                                         |
      | (static files /static, /media)          v
      |                                  [FastAPI Application]
      |                                   |-- Auth Module
      |                                   |-- Event Management Module
      |                                   |-- Weather Monitoring Module --> [OpenWeatherMap API]
      |                                   |-- Risk Analysis Engine
      |                                   |-- Recommendation Engine
      |                                   |-- Dashboard/Reporting Module
      |                                         |
      |                                         v
      |                                  [PostgreSQL Database]
      |
[CLI Tool: weather-cli] -- (jalan terpisah di server, akses langsung) --> [OpenWeatherMap API]
```

### 3.3 Folder Structure (rekomendasi)

```
eventguard/
├── app/
│   ├── main.py                  # entrypoint FastAPI
│   ├── config.py                # load env vars (Pydantic Settings)
│   ├── database.py              # SQLAlchemy engine/session
│   ├── models/
│   │   ├── user.py
│   │   ├── event.py
│   │   ├── weather_log.py
│   │   └── risk_analysis.py
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── auth_schema.py
│   │   ├── event_schema.py
│   │   └── weather_schema.py
│   ├── routers/
│   │   ├── auth_router.py
│   │   ├── event_router.py
│   │   ├── weather_router.py
│   │   ├── dashboard_router.py
│   │   └── landing_router.py
│   ├── services/
│   │   ├── openweather_service.py   # konsumsi API eksternal
│   │   ├── risk_engine.py           # logika hitung risk
│   │   └── recommendation_engine.py
│   ├── core/
│   │   ├── security.py          # JWT, hashing
│   │   └── deps.py              # dependency injection (get_current_user dll)
│   └── templates/               # Jinja2 HTML (landing, dashboard, login)
├── cli/
│   └── weather_cli.py           # Typer CLI standalone
├── alembic/                     # migration scripts
├── tests/
├── .env.development
├── .env.production
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── gunicorn_config.py
├── README.md
└── deploy/
    ├── eventguard.service        # systemd unit file
    └── nginx_eventguard.conf
```

---

## 4. SKEMA DATABASE (DETAIL)

### Tabel: users
| Kolom | Tipe | Constraint |
|---|---|---|
| id | UUID / SERIAL | PRIMARY KEY |
| name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(150) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| subscription_tier | VARCHAR(20) | DEFAULT 'free' (free/pro/enterprise) |
| created_at | TIMESTAMP | DEFAULT now() |

### Tabel: events
| Kolom | Tipe | Constraint |
|---|---|---|
| id | UUID / SERIAL | PRIMARY KEY |
| user_id | FK -> users.id | NOT NULL |
| name | VARCHAR(150) | NOT NULL |
| location | VARCHAR(200) | NOT NULL |
| latitude | FLOAT | nullable (hasil geocoding) |
| longitude | FLOAT | nullable |
| event_date | DATE | NOT NULL |
| start_time | TIME | NOT NULL |
| end_time | TIME | NOT NULL |
| status | VARCHAR(20) | DEFAULT 'upcoming' (upcoming/active/done) |
| created_at | TIMESTAMP | DEFAULT now() |

### Tabel: weather_logs
| Kolom | Tipe | Constraint |
|---|---|---|
| id | UUID / SERIAL | PRIMARY KEY |
| event_id | FK -> events.id | NOT NULL |
| temperature | FLOAT | |
| humidity | FLOAT | |
| wind_speed | FLOAT | |
| cloud_coverage | FLOAT | |
| rain_probability | FLOAT | |
| source_env | VARCHAR(20) | 'live' atau 'mock' — pembeda staging/production |
| fetched_at | TIMESTAMP | DEFAULT now() |

### Tabel: risk_analysis
| Kolom | Tipe | Constraint |
|---|---|---|
| id | UUID / SERIAL | PRIMARY KEY |
| event_id | FK -> events.id | NOT NULL |
| rain_risk | VARCHAR(10) | LOW/MEDIUM/HIGH |
| wind_risk | VARCHAR(10) | LOW/MEDIUM/HIGH |
| heat_risk | VARCHAR(10) | LOW/MEDIUM/HIGH |
| overall_risk | VARCHAR(10) | LOW/MEDIUM/HIGH |
| recommendation | TEXT | |
| analyzed_at | TIMESTAMP | DEFAULT now() |

---

## 5. DAFTAR ENDPOINT API

### Auth
```
POST   /api/auth/register      -> register user baru
POST   /api/auth/login         -> login, return JWT
POST   /api/auth/logout        -> invalidate token (client-side discard / blacklist)
```

### Event Management
```
POST   /api/events             -> buat event baru (trigger fetch cuaca otomatis)
GET    /api/events             -> list semua event milik user
GET    /api/events/{id}        -> detail satu event
PUT    /api/events/{id}        -> edit event
DELETE /api/events/{id}        -> hapus event
```

### Weather Monitoring
```
GET    /api/events/{id}/weather          -> ambil weather log terbaru event
GET    /api/events/{id}/weather/history  -> histori semua weather log event
POST   /api/events/{id}/weather/refresh  -> trigger re-fetch cuaca manual
```

### Risk Analysis
```
GET    /api/events/{id}/risk             -> hasil analisis risiko terbaru
POST   /api/events/{id}/risk/analyze     -> trigger ulang kalkulasi risiko
```

### Dashboard
```
GET    /api/dashboard/summary  -> jumlah event, event aktif, mendatang, risiko tinggi
```

### Landing Page (non-API, render HTML)
```
GET    /                       -> landing page (hero, features, pricing, contact)
GET    /login
GET    /register
GET    /dashboard              -> halaman dashboard setelah login
```

---

## 6. LOGIKA BISNIS

### 6.1 Weather Monitoring Flow
1. User membuat event baru dengan field: nama, lokasi (nama kota/alamat), tanggal, jam mulai, jam selesai.
2. Sistem memanggil OpenWeatherMap Geocoding API untuk mengubah nama lokasi menjadi koordinat (lat/lon).
3. Sistem memanggil OpenWeatherMap Current Weather / Forecast API menggunakan koordinat tersebut, menyasar tanggal event (gunakan forecast endpoint jika event_date di masa depan).
4. Response JSON dari OpenWeatherMap di-mapping (bukan diteruskan mentah) ke struktur weather_logs: temperature, humidity, wind_speed, cloud_coverage, rain_probability.
5. Data disimpan ke tabel weather_logs dengan source_env sesuai environment aktif.

### 6.2 Risk Analysis Engine
Logika kalkulasi risiko (contoh threshold, boleh disesuaikan):

```
Rain Risk:
  rain_probability >= 70%  -> HIGH
  rain_probability 30-69%  -> MEDIUM
  rain_probability < 30%   -> LOW

Wind Risk:
  wind_speed >= 15 m/s     -> HIGH
  wind_speed 8-14.9 m/s    -> MEDIUM
  wind_speed < 8 m/s       -> LOW

Heat Risk:
  temperature >= 35°C      -> HIGH
  temperature 30-34.9°C    -> MEDIUM
  temperature < 30°C       -> LOW

Overall Risk:
  Jika minimal 1 kategori HIGH        -> overall = HIGH
  Jika tidak ada HIGH tapi ada MEDIUM -> overall = MEDIUM
  Jika semua LOW                      -> overall = LOW
```

### 6.3 Recommendation Engine
Rule-based, dipetakan dari kondisi cuaca ke teks rekomendasi:

```
IF rain_probability > 70%:
   "Disarankan menyediakan tenda atau memindahkan acara ke lokasi indoor."

IF temperature > 35°C:
   "Disarankan menyediakan area istirahat dan air minum tambahan."

IF wind_speed >= 15 m/s:
   "Disarankan mengamankan tenda, banner, dan peralatan ringan dari risiko terbang."

IF overall_risk == LOW:
   "Kondisi cuaca diperkirakan aman untuk pelaksanaan acara outdoor."
```

Rekomendasi bisa digabung (concatenate) jika lebih dari satu kondisi terpenuhi.

### 6.4 Dashboard Aggregation
```
total_event        = COUNT(events WHERE user_id = current_user)
active_event       = COUNT(events WHERE status = 'active')
upcoming_event      = COUNT(events WHERE event_date > today)
high_risk_event     = COUNT(events JOIN risk_analysis WHERE overall_risk = 'HIGH')
```

---

## 7. MULTI-ENVIRONMENT STRATEGY (untuk pemenuhan UTS Soal 3)

### .env.development
```
APP_ENV=development
PORT=3001
DATABASE_URL=postgresql://eventguard_dev:devpass@localhost:5432/eventguard_dev
OPENWEATHER_API_KEY=dummy_or_real_key_with_low_quota_usage
OPENWEATHER_MODE=mock          # pakai data JSON statis, hindari boros quota
JWT_SECRET=dev-secret-not-for-prod
```

### .env.production
```
APP_ENV=production
PORT=80
DATABASE_URL=postgresql://eventguard_prod:strongpass@db-host:5432/eventguard_prod
OPENWEATHER_API_KEY=real_production_key
OPENWEATHER_MODE=live          # panggilan asli ke OpenWeatherMap
JWT_SECRET=long-random-production-secret
```

**Implementasi kode kunci:** `openweather_service.py` membaca `OPENWEATHER_MODE`. Jika `mock`, return data dari file JSON statis lokal (`mock_data/sample_weather.json`) tanpa hit API eksternal sama sekali. Jika `live`, lakukan HTTP request asli ke OpenWeatherMap. Ini membuktikan "aplikasi dapat berpindah environment tanpa mengubah kode" — hanya ganti file `.env` dan environment variable terbaca otomatis lewat Pydantic Settings.

Port juga dibedakan: development jalan di 3001, production di 80 (di-reverse-proxy nginx kalau pakai HTTPS 443).

---

## 8. CLI TOOL (UTS Requirement)

Nama command: `weather-cli`

```bash
weather-cli --city Kendari
```

Output yang diharapkan (contoh):
```
Fetching weather data for: Kendari
-----------------------------------
Temperature     : 29.5°C
Humidity        : 78%
Rain Chance     : 65%
Wind Speed      : 6.2 m/s
Cloud Coverage  : 80%
-----------------------------------
Source: OpenWeatherMap (live)
```

Implementasi: file `cli/weather_cli.py` menggunakan Typer, memanggil `openweather_service.py` yang sama dengan yang dipakai aplikasi web (reuse kode, bukan duplikasi), dijalankan langsung dari terminal server (bukan dari endpoint HTTP). Pasang sebagai executable lewat `setup.py`/`pyproject.toml` entry_points, atau alias shell sederhana, supaya bisa dipanggil dengan `weather-cli` tanpa `python weather_cli.py`.

---

## 9. LANDING PAGE SAAS (UAS Requirement)

Struktur halaman `/` (single page, 4 section wajib):

**Hero Section:** Judul utama ("Pantau Risiko Cuaca Acara Outdoor Anda Sebelum Terlambat"), subjudul singkat, CTA button "Mulai Gratis" / "Lihat Demo".

**Features Section:** 4-6 card menampilkan fitur utama — Weather Monitoring otomatis, Risk Analysis (LOW/MEDIUM/HIGH), Recommendation Engine, Dashboard multi-event, Weather History.

**Pricing Section (simulasi, tidak ada payment gateway sungguhan):**
```
FREE          PRO              ENTERPRISE
Rp 0/bulan    Rp 99.000/bulan  Rp 499.000/bulan
- 3 Event     - 50 Event       - Unlimited Event
- Basic       - Weather        - External API
  Weather       History          Access
  Check       - Advanced       - Priority
              Risk Analysis      Support
```

**Contact Section:** Form sederhana (nama, email, pesan) — submit boleh hanya simulasi (tidak perlu kirim email asli, cukup tampilkan toast "Pesan terkirim").

---

## 10. DEPLOYMENT FLOW (UAS Requirement, urutan lengkap)

1. **Provisioning VPS** — pastikan Ubuntu Server terbaru, akses root/sudo.
2. **SSH Remote** ke VPS dari laptop tim.
3. **Install dependencies dasar di server:** Python 3.12, pip, venv, PostgreSQL, nginx, git.
4. **Clone repository** dari GitHub ke server (`git clone <repo_url>`).
5. **Setup virtual environment & install package:** `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
6. **Setup `.env.production`** di server (isi berbeda dari `.env.development` di laptop — buktikan dengan `cat` kedua file, JANGAN expose API key asli di screenshot laporan, sensor sebagian).
7. **Jalankan migration database:** `alembic upgrade head`.
8. **Test jalankan manual dengan Gunicorn:**
   ```
   gunicorn -w 3 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8000
   ```
9. **Buat systemd service** (`/etc/systemd/system/eventguard.service`):
   ```ini
   [Unit]
   Description=EventGuard FastAPI Service
   After=network.target

   [Service]
   User=deploy
   Group=www-data
   WorkingDirectory=/home/deploy/eventguard
   Environment="PATH=/home/deploy/eventguard/.venv/bin"
   EnvironmentFile=/home/deploy/eventguard/.env.production
   ExecStart=/home/deploy/eventguard/.venv/bin/gunicorn -w 3 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8000
   Restart=always
   RestartSec=3

   [Install]
   WantedBy=multi-user.target
   ```
   Aktifkan: `sudo systemctl enable --now eventguard`.
10. **Konfigurasi Nginx reverse proxy** (`/etc/nginx/sites-available/eventguard`):
    ```nginx
    server {
        listen 80;
        server_name namadomain.online www.namadomain.online;

        location /static/ {
            alias /home/deploy/eventguard/app/static/;
        }

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    ```
    Symlink ke `sites-enabled`, test `nginx -t`, reload `systemctl reload nginx`.
11. **Beli domain `.online`** dan arahkan A record ke IP VPS.
12. **Install Certbot:** `sudo apt install certbot python3-certbot-nginx`, lalu `sudo certbot --nginx -d namadomain.online -d www.namadomain.online`.
13. **Set permission folder media/static** agar `www-data` bisa akses: `sudo chown -R deploy:www-data /home/deploy/eventguard/app/static`.
14. **Verifikasi akhir:** akses `https://namadomain.online` dari browser, pastikan SSL valid, test register/login/buat event end-to-end.
15. **(Opsional nilai tambah) Dockerize:** siapkan `Dockerfile` + `docker-compose.yml` (service: app, db, nginx) sebagai alternatif deployment, jalankan `docker compose up -d --build` sebagai bukti tambahan kemampuan containerization.

---

## 11. MAPPING LANGSUNG KE RUBRIK PENILAIAN

| Item Rubrik | Bukti di EventGuard |
|---|---|
| Konsumsi RESTful API (30) | OpenWeatherMap dipanggil di `openweather_service.py`, dipakai saat create event & CLI |
| Pengolahan response (10 dari 30) | Mapping JSON OpenWeatherMap -> struktur weather_logs di service layer |
| Error handling (10 dari 30) | Handle: kota tidak ditemukan, timeout, API key invalid, rate limit 429 |
| Manajemen API Key (20) | `.env` + `.gitignore`, README jelas cara isi key |
| Multi Environment (35) | `.env.development` (mock, port 3001) vs `.env.production` (live, port 80), tanpa ubah kode |
| CLI Integration | `weather-cli --city <nama>` reuse service layer yang sama |
| Deploy VPS (UAS) | Urutan lengkap section 10 di atas, dengan bukti screenshot tiap tahap |
| Landing Page SaaS (UAS) | Section 9 — Hero, Features, Pricing, Contact |

---

Teks ini sudah saya susun supaya bisa langsung kamu paste ke Antigravity sebagai instruksi pembuatan proyek end-to-end (struktur folder, model, endpoint, logic, env, deployment). Kalau Antigravity butuh detail tambahan seperti contoh response JSON OpenWeatherMap mentah atau skema validasi Pydantic per endpoint, kabari saja, saya lengkapi.