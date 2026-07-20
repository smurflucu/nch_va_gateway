# 📱 Nch WA Gateway — WhatsApp Gateway Multi-User (Baileys)

WhatsApp gateway **tidak resmi** berbasis [Baileys](https://github.com/WhiskeySockets/Baileys),
dengan dashboard **multi-level user** (admin / supervisor / regular), isolasi antar-tim,
dan alur approval broadcast. Cocok untuk tim CS / marketing yang mengelola banyak nomor WA.

> ⚠️ **Non-resmi.** Memakai WhatsApp lewat Baileys melanggar ToS WhatsApp — nomor bisa
> diblokir kalau kirim terlalu masif. Pakai nomor yang siap "dikorbankan", hormati opt-out.
> Untuk skala serius, pertimbangkan **WhatsApp Business API resmi**.

---

## Arsitektur

```
┌──────────┐   HTTP (JWT)    ┌─────────────┐  HTTP internal   ┌────────────────┐
│ Frontend │ ───────────────▶│  FastAPI    │ ────────────────▶│  wa-gateway    │
│ (React)  │                 │  "otak"     │◀──── webhook ────│  (Node+Baileys)│──▶ WhatsApp
└──────────┘                 └─────────────┘   (event/pesan)  └────────────────┘
   :8080 (nginx)              backend :8000                      wa-gateway :3001
   serve UI + proxy /api      auth, RBAC, data                   pegang koneksi WA
```

| Service | Stack | Peran |
|---|---|---|
| **frontend** | React 18 + Vite + zustand | Dashboard SPA, di-serve nginx + reverse-proxy `/api` ke backend |
| **backend** | FastAPI + SQLAlchemy | Semua logika bisnis: auth, RBAC, kontak, template, broadcast, log |
| **wa-gateway** | Node + Baileys 7 | Engine WhatsApp: sesi multi-nomor, QR login, kirim/terima. **Tidak diekspos publik** |

Dokumen teknis lengkap: [docs/BACKEND.md](docs/BACKEND.md) · [docs/FRONTEND.md](docs/FRONTEND.md)

---

## Menjalankan (Docker — cara termudah)

```bash
cp .env.example .env          # konfigurasi database (default: Postgres lokal)
docker compose up -d --build
# App:      http://localhost:8080
# API docs: http://localhost:8080/docs
```

Compose menyalakan service backend, wa-gateway, frontend, + **Postgres** (bila
`COMPOSE_PROFILES=localdb` di `.env`), dengan volume persisten:
- `wa-auth` — kredensial WhatsApp (biar tidak scan ulang tiap restart)
- `pg-data` — data PostgreSQL

### Database (Postgres) — gampang di-switch

Semua diatur di **`.env` (root)** — cukup edit 2 baris:

| Mode | `COMPOSE_PROFILES` | `DATABASE_URL` |
|---|---|---|
| **Postgres lokal (Docker)** — default | `localdb` | `postgresql+psycopg://wa_user:wa_password@db:5432/wa_gateway` |
| **Supabase** | *(kosong)* | URI dari Supabase (Session pooler) + `?sslmode=require` |
| **Postgres di host** | *(kosong)* | `postgresql+psycopg://user:pass@host.docker.internal:5432/db` |

Skema tabel dibuat otomatis saat backend start (`create_all` + migrasi ringan). Detail:
[docs/BACKEND.md](docs/BACKEND.md#database--migrasi). Contoh Supabase ada di `.env.example`.

**User pertama yang register otomatis jadi admin.** Belum ada halaman sign-up di UI, jadi
buat admin lewat API:

```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@contoh.com","password":"rahasia123","full_name":"Admin"}'
```

Lalu login di http://localhost:8080 dan buat supervisor + regular user lewat menu **Tim & User**.

### Menjalankan tanpa Docker (dev, 3 terminal)

```bash
# 1) wa-gateway (Node)
cd wa-gateway && cp .env.example .env && npm install && npm start   # :3001

# 2) backend (FastAPI)
cd backend && cp .env.example .env      # ganti SECRET_KEY & samakan token dgn wa-gateway
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload            # :8000, docs di /docs

# 3) frontend
cd frontend && npm install && npm run dev  # :5173 (proxy /api ke :8000)
```

---

## Role & hak akses

Hirarki: **admin > supervisor > regular user**. "Tim" = satu supervisor + semua regular
user di bawahnya (`User.supervisor_id`). Antar-supervisor **tidak saling melihat**.

| Kemampuan | Admin | Supervisor | Regular |
|---|:---:|:---:|:---:|
| Input & assign nomor WA | ✅ | — | — |
| Lihat semua data | ✅ | — | — |
| Lihat data tim (diri + regular-nya) | (semua) | ✅ | — |
| Kirim pesan | ✅ | ✅ | ✅ (nomor tim) |
| Lihat inbox | semua | tim | **percakapan sendiri** |
| Kelola kontak & template | ✅ | ✅ (tim) | read-only |
| Buat broadcast | ✅ | ✅ | ✅ **butuh approval** |
| Approve/tolak broadcast | ✅ | ✅ | — |
| Kelola user | semua | anggota tim | — |

Detail scoping: [docs/BACKEND.md#rbac--isolasi-tim](docs/BACKEND.md).

---

## Fitur

| Fitur | Menu | Catatan |
|---|---|---|
| Multi-nomor + QR login | **Nomor WA** | Input & assign nomor: admin saja |
| Kirim pesan satuan | **Kirim Pesan** | — |
| Inbox (masuk & keluar) | **Inbox** | Regular hanya lihat percakapan yang ia mulai |
| Broadcast/blast + jeda anti-ban + `{{name}}` | **Broadcast** | Regular → antrian approval |
| Broadcast terjadwal | **Broadcast** | Pakai scheduler bawaan |
| Auto-reply berdasarkan kata kunci | **Auto-Reply** | Level tim (supervisor/admin) |
| Kontak & Template | **Kontak**, **Template** | Level tim |
| Tim & User (buat/edit/hapus, assign) | **Tim & User** | Admin: semua; supervisor: anggota tim |
| API untuk aplikasi eksternal | **API Gateway** | Kirim via `X-API-Key` |
| Scheduler / cron | **Jobs** | Admin saja |

---

## API untuk aplikasi eksternal

```bash
curl -X POST http://localhost:8080/api/v1/gateway/send \
  -H "X-API-Key: wa_xxxx_yyyy" \
  -H "Content-Type: application/json" \
  -d '{"session_id": 1, "to": "0812xxxxxxx", "text": "Halo dari API"}'
```

Buat API-key di menu **API Gateway** (ditampilkan **sekali** saat dibuat).

---

## Keamanan & operasional

- `WA_INTERNAL_TOKEN` & `WEBHOOK_SECRET` **harus identik** di `backend/.env` dan
  `wa-gateway/.env` (di Docker diset lewat `environment:`). **Ganti sebelum production.**
- Service `wa-gateway` **jangan** diekspos ke internet (di compose hanya `expose`, bukan `ports`).
- **JWT:** access token 15 menit di memory (aman dari XSS) + refresh token 7 hari di httpOnly
  cookie dengan rotasi.
- **"Waiting for this message" / LID:** wa-gateway pakai Baileys 7 dengan `getMessage` (retry)
  dan resolusi LID→nomor. Kalau nomor stuck "waiting", **re-pair** (hapus sesi + scan ulang)
  untuk membersihkan sesi enkripsi basi. Lihat komentar di `wa-gateway/server.js`.

### Checklist sebelum production

- [ ] Ganti `SECRET_KEY` (`openssl rand -hex 32`), `WA_INTERNAL_TOKEN`, `WEBHOOK_SECRET`
- [ ] `COOKIE_SECURE=true`, `DEBUG=false`, `ENV=production`
- [ ] `CORS_ORIGINS` isi domain asli saja
- [ ] HTTPS di depan (nginx/Cloudflare/LB)
- [ ] Ganti `create_all`/`migrate.py` → **Alembic** migration (skema versioned)
- [ ] Secret ke Secret Manager / vault, bukan file `.env`

---

## Struktur repo

```
backend/     FastAPI — lihat docs/BACKEND.md
frontend/    React/Vite — lihat docs/FRONTEND.md
wa-gateway/  Node + Baileys (engine WhatsApp)
docs/        Dokumentasi teknis
docker-compose.yml
```
