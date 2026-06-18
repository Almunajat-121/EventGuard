# Konsep Frontend EventGuard

Dokumen ini adalah konsep frontend yang disesuaikan dengan `konsep.md`, `konsep_updated.md`, dan kondisi project EventGuard saat ini.

Tujuan frontend: membuat EventGuard terasa seperti aplikasi SaaS yang siap dipakai oleh event organizer untuk memantau risiko cuaca per acara, bukan sekadar halaman demo.

## 1. Prinsip Frontend

Frontend EventGuard menggunakan pendekatan hybrid:

- Jinja2 untuk halaman utama, auth, dan shell dashboard.
- Fetch API untuk mengambil data dashboard secara dinamis.
- Chart.js untuk visualisasi ringkas.
- TailwindCSS CDN untuk styling cepat.
- JWT disimpan dalam HttpOnly cookie, sehingga frontend tidak menyimpan token di `localStorage`.

Karena auth memakai HttpOnly cookie, semua request fetch yang membutuhkan login sebaiknya memakai:

```javascript
credentials: "include"
```

Walaupun same-origin biasanya otomatis mengirim cookie, penggunaan eksplisit ini lebih sesuai dengan `konsep_updated.md`.

## 2. Struktur Halaman

Frontend minimal terdiri dari halaman berikut:

```text
/
/login
/register
/dashboard
```

Opsional jika ingin lebih rapi:

```text
/events/{id}
/settings
```

Untuk versi MVP, detail event cukup ditampilkan melalui modal di dashboard.

## 3. Landing Page

File target: `app/templates/index.html`

Landing page wajib punya 4 section:

### 3.1 Hero

Tujuan: langsung menjelaskan nilai utama EventGuard.

Konten:

- Headline: `Pantau Risiko Cuaca Acara Outdoor Anda`
- Subheadline: jelaskan bahwa sistem memantau risiko hujan, angin, dan panas ekstrem.
- CTA utama: `Mulai Gratis`
- CTA sekunder: `Lihat Dashboard Demo` atau scroll ke fitur.

Catatan:

- Jangan hanya hero kosong.
- Harus terasa sebagai SaaS untuk event outdoor.

### 3.2 Features

Tampilkan 4-6 fitur utama:

- Monitoring Cuaca Otomatis
- Risk Analysis LOW/MEDIUM/HIGH
- Rekomendasi Tindakan
- Dashboard Multi-Event
- Weather History
- Notifikasi Risiko Tinggi

Setiap fitur cukup berisi ikon, judul, dan deskripsi pendek.

### 3.3 Pricing

Tampilkan 3 paket:

```text
FREE
Rp 0/bulan
- 3 event
- Basic weather check
- Manual refresh

PRO
Rp 99.000/bulan
- 50 event
- Weather history
- Advanced risk analysis
- In-app notification

ENTERPRISE
Rp 499.000/bulan
- Unlimited event
- Priority support
- External API access
- Custom monitoring interval
```

Tidak perlu payment gateway. Pricing hanya simulasi SaaS.

### 3.4 Contact

Form sederhana:

- Nama
- Email
- Pesan

Submit cukup simulasi di frontend:

```javascript
alert("Pesan terkirim. Tim EventGuard akan menghubungi Anda.");
```

## 4. Auth Pages

File target:

- `app/templates/login.html`
- `app/templates/register.html`

Auth harus sederhana dan jelas.

### 4.1 Login

Field:

- Email
- Password

Behavior:

- Submit ke `POST /api/auth/login`.
- Jika berhasil, redirect ke `/dashboard`.
- Jika gagal, tampilkan error di halaman, bukan hanya console.

Fetch:

```javascript
fetch("/api/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "include",
  body: JSON.stringify({ email, password })
})
```

### 4.2 Register

Field:

- Nama
- Email
- Password

Behavior:

- Submit ke `POST /api/auth/register`.
- Setelah berhasil, otomatis login atau arahkan ke `/login`.
- Untuk demo, auto-login boleh dipakai.

## 5. Dashboard

File target: `app/templates/dashboard.html`

Dashboard adalah layar utama aplikasi, bukan halaman promosi.

Layout yang disarankan:

```text
Top navigation:
- EventGuard
- Notification bell
- Logout

Summary cards:
- Total Event
- Upcoming Event
- High Risk Event
- Subscription Tier

Main content:
- Daftar event
- Filter status/risk
- Tombol buat event

Side/modal:
- Detail event
- Weather snapshot
- Risk analysis
- Recommendation
- Notification
```

## 6. Dashboard Summary

Endpoint:

```text
GET /api/dashboard/summary
```

Tampilkan:

- Total events
- Upcoming events
- High risk events
- Subscription tier

Catatan:

- Jika API gagal, tampilkan fallback text.
- Jangan biarkan UI terus menampilkan `-` tanpa pesan.

## 7. Event List

Endpoint:

```text
GET /api/events
```

Setiap item event menampilkan:

- Nama event
- Lokasi
- Tanggal mulai dan selesai
- Jam mulai dan selesai
- Forecast status: `AVAILABLE`, `TOO_FAR`, atau `PASSED`
- Tombol `Update Cuaca` jika forecast tersedia
- Tombol `Detail`

Status badge:

- AVAILABLE: hijau
- TOO_FAR: kuning
- PASSED: abu-abu

## 8. Create Event Modal

Endpoint:

```text
POST /api/events
```

Field:

- Nama acara
- Lokasi
- Tanggal mulai
- Tanggal selesai
- Jam mulai
- Jam selesai
- Timezone, default `Asia/Jakarta`

Validasi frontend:

- Nama wajib.
- Lokasi wajib.
- Tanggal selesai tidak boleh sebelum tanggal mulai.
- Jam selesai harus masuk akal untuk event satu hari.
- Tampilkan error dari backend jika free tier sudah mencapai 3 event.

Setelah berhasil:

- Tutup modal.
- Reset form.
- Reload event list dan summary.

## 9. Weather Refresh

Endpoint:

```text
POST /api/events/{event_id}/weather/refresh
```

Behavior UI:

- Saat tombol diklik, ubah tombol menjadi loading.
- Jangan gunakan `alert()` untuk loading utama.
- Setelah berhasil, tampilkan toast atau pesan kecil.
- Reload event list, summary, dan detail jika modal sedang terbuka.

Contoh state:

```text
Update Cuaca -> Memperbarui... -> Berhasil diperbarui
```

## 10. Event Detail Modal

Endpoint MVP:

```text
GET /api/events/{event_id}/details
```

Detail modal menampilkan:

- Nama event
- Lokasi
- Tanggal dan jam acara
- Suhu worst-case
- Peluang hujan worst-case
- Kecepatan angin worst-case
- Jam worst-case
- Risk badge: LOW/MEDIUM/HIGH/PENDING
- Rekomendasi sistem

Jika belum ada data cuaca:

```text
Data cuaca belum tersedia. Klik Update Cuaca untuk melakukan analisis pertama.
```

Risk badge:

- LOW: hijau
- MEDIUM: kuning
- HIGH: merah
- PENDING: abu-abu

## 11. Chart.js

Chart minimal untuk memenuhi konsep dashboard interaktif:

### Opsi A: Risk Distribution

Chart donut:

- LOW
- MEDIUM
- HIGH
- PENDING

Endpoint ideal:

```text
GET /api/dashboard/risk-distribution
```

Jika endpoint belum ada, data bisa dihitung sementara dari event detail, tetapi lebih baik backend menyediakan endpoint khusus.

### Opsi B: Event Status Distribution

Chart bar:

- Upcoming
- Active
- Done

Endpoint ideal:

```text
GET /api/dashboard/summary
```

Jika summary belum menyediakan semua data, tambahkan `active_events` dan `done_events`.

## 12. Notifications UI

Endpoint:

```text
GET /api/notifications
PATCH /api/notifications/{id}/read
```

UI:

- Tambahkan ikon/badge notifikasi di navbar dashboard.
- Tampilkan jumlah unread.
- Klik badge membuka dropdown/list notifikasi.
- Setiap notifikasi bisa ditandai sudah dibaca.

Isi notifikasi:

```text
Peringatan! Risiko cuaca untuk acara "Nama Event" meningkat menjadi HIGH.
```

## 13. Empty State

Dashboard harus punya empty state yang ramah.

Jika belum ada event:

```text
Belum ada acara yang dipantau.
Buat event pertama Anda untuk mulai menganalisis risiko cuaca.
```

Tombol:

```text
Buat Event
```

## 14. Error State

Untuk error API:

- Jangan hanya `console.error`.
- Tampilkan pesan kecil di UI.
- Untuk error penting, gunakan toast.

Contoh:

```text
Gagal memuat data dashboard. Silakan coba lagi.
```

## 15. Loading State

Tambahkan loading state untuk:

- Load summary
- Load event list
- Create event
- Refresh weather
- Load detail
- Load notifications

Loading state cukup sederhana, misalnya:

```text
Memuat data...
```

atau skeleton kecil.

## 16. Visual Style

Karakter UI:

- Bersih
- Profesional
- SaaS dashboard
- Tidak terlalu ramai
- Cocok untuk event organizer

Warna status:

```text
LOW       : hijau
MEDIUM    : kuning
HIGH      : merah
PENDING   : abu-abu
AVAILABLE : hijau
TOO_FAR   : kuning
PASSED    : abu-abu
```

Gunakan konsistensi warna di seluruh dashboard.

## 17. Responsiveness

Minimal harus nyaman di:

- Desktop laptop
- Tablet
- Mobile

Pada mobile:

- Summary card menjadi 1 kolom.
- Event list menjadi stacked layout.
- Modal detail memakai lebar hampir penuh.
- Navbar tetap sederhana.

## 18. Endpoint yang Dibutuhkan Frontend

Frontend ideal membutuhkan endpoint berikut:

```text
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout

GET    /api/dashboard/summary

GET    /api/events
POST   /api/events
GET    /api/events/{id}
PUT    /api/events/{id}
DELETE /api/events/{id}

GET    /api/events/{id}/details
GET    /api/events/{id}/weather
GET    /api/events/{id}/weather/history
POST   /api/events/{id}/weather/refresh

GET    /api/events/{id}/risk
POST   /api/events/{id}/risk/analyze

GET    /api/notifications
PATCH  /api/notifications/{id}/read
```

Untuk MVP sekarang, minimal frontend bisa berjalan dengan:

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/dashboard/summary
GET  /api/events
POST /api/events
GET  /api/events/{id}/details
POST /api/events/{id}/weather/refresh
GET  /api/notifications
PATCH /api/notifications/{id}/read
```

## 19. Review Kondisi Frontend Saat Ini

Frontend saat ini sudah punya:

- Landing page dasar.
- Login page.
- Register page.
- Dashboard summary.
- Event list.
- Modal create event.
- Modal detail event.
- Refresh weather button.

Frontend yang masih kurang:

- Landing page belum punya features, pricing, dan contact.
- Dashboard belum memakai Chart.js walau script sudah dimuat.
- Fetch belum eksplisit memakai `credentials: "include"`.
- Belum ada UI notifikasi.
- Belum ada toast/loading state yang rapi.
- Detail event bergantung pada endpoint backend yang saat ini masih punya bug sorting field.
- Error handling masih banyak memakai `alert()` dan `console.error`.

## 20. Prioritas Implementasi FE

Urutan pengerjaan yang disarankan:

1. Lengkapi landing page: hero, features, pricing, contact.
2. Tambahkan `credentials: "include"` ke semua fetch yang berhubungan dengan auth/session.
3. Perbaiki loading dan error state di dashboard.
4. Tambahkan UI notification badge dan dropdown.
5. Tambahkan Chart.js sederhana untuk risk atau event status.
6. Rapikan modal detail event agar menampilkan worst-case time.
7. Tambahkan edit/delete event jika backend endpoint sudah tersedia.
8. Kurangi penggunaan `alert()` dan ganti dengan toast sederhana.

## 21. Kriteria Selesai

Frontend dianggap sesuai konsep jika:

- User bisa register, login, dan logout.
- User bisa membuat event.
- User bisa melihat daftar event.
- User bisa refresh cuaca.
- User bisa melihat hasil risk analysis dan rekomendasi.
- Dashboard menampilkan summary.
- Dashboard punya minimal satu chart.
- User bisa melihat notifikasi risiko tinggi.
- Landing page memiliki hero, features, pricing, dan contact.
- Fetch API bekerja dengan HttpOnly cookie.
- Tampilan tetap rapi di desktop dan mobile.

## Kesimpulan

Konsep frontend EventGuard harus diarahkan sebagai dashboard SaaS operasional untuk monitoring risiko cuaca event outdoor.
Saat ini frontend sudah punya dasar yang cukup, tetapi masih perlu dilengkapi agar sesuai `konsep_updated.md`, terutama pada landing page, dashboard interaktif, notification UI, Chart.js, dan state handling.
