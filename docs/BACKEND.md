# Backend — Technical Reference

FastAPI (Python 3.12) dengan arsitektur berlapis. Fokus: **RBAC multi-tim** di atas
WhatsApp gateway. Satu-satunya tempat baca environment: `app/core/config.py`.

## Stack

- **FastAPI** + **Uvicorn** — HTTP
- **SQLAlchemy 2.x** (Mapped/`mapped_column`) — ORM
- **PostgreSQL** (driver `psycopg` v3, dialect `postgresql+psycopg`) — lokal via Docker
  atau Supabase/eksternal, diatur dari `.env` root. (SQLite masih didukung engine untuk
  dev cepat, tapi setup default = Postgres.)
- **APScheduler** — scheduler embedded (broadcast terjadwal, jobs)
- **slowapi** — rate limit · **bcrypt** — hash password · **python-jose** — JWT
- **httpx/requests** — panggil Node wa-gateway

## Arah dependency

```
api (HTTP only) → services (business logic) → repositories (query) → db
```

Endpoint **dilarang** akses DB langsung; lewat service. Service tidak tahu soal HTTP.

## Struktur

```
app/
  api/
    deps.py               # DI + guard RBAC (get_current_user, require_admin, dll)
    v1/router.py          # daftar semua router
    v1/endpoints/         # HTTP: auth, users, sessions, messaging, contacts,
                          #       templates, broadcasts, autoreplies, apikeys,
                          #       gateway (API-key), wa_webhook, jobs, health
  core/                   # config, security (JWT+bcrypt), logging, exceptions
  db/
    session.py            # engine + SessionLocal + Base + get_db
    migrate.py            # migrasi ringan SQLite + bootstrap admin
  models/                 # SQLAlchemy: user, wa, job
  schemas/                # Pydantic: user, wa, token, job
  services/
    scope.py              # ⭐ aturan visibilitas RBAC (team scoping)
    user_service.py, wa_service.py, broadcast_service.py,
    apikey_service.py, scheduler_service.py, wa_gateway_client.py
  repositories/           # base + user_repository + wa_repository
  middlewares/            # logging, rate limit, security headers
  tasks/                  # background jobs (broadcast dispatch, dll)
  utils/                  # validators (normalize_phone), dll
  main.py                 # bootstrap: create_all + migrate + CORS + router + scheduler
```

---

## Auth flow

1. `POST /auth/login` → **access token (15 mnt)** di body + **refresh token (7 hari)** di
   **httpOnly cookie** (`path=/api/v1/auth`, `SameSite`, `Secure` opsional).
2. Client simpan access token **di memory** (bukan localStorage → aman XSS).
3. `401` → client panggil `POST /auth/refresh` (cookie ikut) → access token baru; refresh
   token **dirotasi**.
4. `get_current_user` (`app/api/deps.py`) baca `Authorization: Bearer`, decode, ambil user aktif.

Registrasi: `POST /auth/register`. **User pertama otomatis `admin`** (bootstrap di
`UserService.register`); sisanya `user` tanpa tim (harus di-assign admin).

---

## RBAC & isolasi tim

### Model

`User` (`app/models/user.py`):
- `role`: `admin` | `supervisor` | `user` (konstanta `ROLE_*`, `VALID_ROLES`)
- `supervisor_id`: FK ke `users.id`. Untuk regular = id supervisor timnya; NULL untuk admin & supervisor.

**Tim** = satu supervisor + semua regular user yang `supervisor_id`-nya menunjuk ke dia.

`WaSession.supervisor_id` = tim pemilik nomor (di-assign admin). `Broadcast.approved_by` +
status `pending_approval` untuk alur approval.

### Guards (`app/api/deps.py`)

| Guard | Lolos untuk |
|---|---|
| `get_current_user` | user terautentikasi |
| `require_admin` | `admin` |
| `require_supervisor_or_admin` | `admin`, `supervisor` |
| `require_role(*roles)` | role yang disebут |
| `get_apikey_user` | pemilik `X-API-Key` valid (endpoint gateway publik) |

### Scope helper (`app/services/scope.py`)

```python
team_owner_id(user)        # id supervisor pemilik tim; None utk admin
team_member_ids(db, owner) # [owner] + regular di bawahnya
visible_user_ids(db, user) # inbox/broadcast: admin=None(all), sup=tim, regular=[dia]
team_scope_ids(db, user)   # kontak/template/sesi: regular ikut lihat data timnya
```

Repository menerima `list[int] | None` (None = tanpa filter / admin) dan memfilter
`... .user_id.in_(ids)`.

### Aturan per-resource

| Resource | Lihat | Tulis |
|---|---|---|
| **Users** | admin: semua · supervisor: tim | admin: semua · supervisor: tambah regular timnya |
| **Sessions (nomor)** | tim (`supervisor_id`) · admin: semua | **create/assign/reconnect/delete: admin saja** |
| **Messages (inbox)** | `visible_user_ids` (regular = dirinya) | kirim: semua role (nomor timnya) |
| **Contacts / Templates / Auto-reply** | `team_scope_ids` (regular read-only) | supervisor/admin |
| **Broadcasts** | `visible_user_ids` | create: semua (regular → `pending_approval`); approve/reject: supervisor/admin |

**Conversation ownership** (inbox regular): pesan keluar dicatat atas nama pengirim
(`Message.user_id`). Pesan **masuk** di-assign ke anggota tim yang **terakhir mengirim** ke
nomor itu (`MessageRepository.last_conversation_owner`), fallback ke pemilik tim. Jadi
regular hanya melihat balasan dari percakapan yang ia mulai.

---

## Endpoint (prefix `/api/v1`)

| Grup | Endpoint | Akses |
|---|---|---|
| auth | `POST /auth/{register,login,refresh,logout}` | publik |
| users | `GET/POST /users`, `GET /users/supervisors`, `POST /users/team`, `PATCH/DELETE /users/{id}`, `GET/PATCH /users/me` | supervisor/admin (lihat guard tiap route) |
| sessions | `GET /sessions`, `POST /sessions`, `PATCH /sessions/{id}/assign`, `GET /sessions/{id}/status`, `POST /sessions/{id}/reconnect`, `DELETE /sessions/{id}` | create/assign/reconnect/delete = admin |
| messages | `POST /messages/send`, `GET /messages` | semua (scoped) |
| contacts / templates / autoreplies | `GET/POST/DELETE (+PATCH autoreplies)` | baca: semua tim · tulis: supervisor/admin |
| broadcasts | `GET /broadcasts`, `GET /broadcasts/pending`, `POST /broadcasts`, `GET /broadcasts/{id}`, `POST /broadcasts/{id}/{approve,reject}` | pending/approve/reject = supervisor/admin |
| apikeys | `GET/POST/DELETE /api-keys` | per-user |
| gateway | `POST /gateway/send` | `X-API-Key` |
| webhook | `POST /wa/webhook` | dari Node (verifikasi `WEBHOOK_SECRET`) |
| jobs | `/jobs...` | admin |

Swagger interaktif: `/docs` (hanya saat `DEBUG=true`).

---

## Alur WhatsApp

1. Admin `POST /sessions` (opsional `supervisor_id`) → `WaService.create_session` simpan
   `WaSession` (status `connecting`) + minta Node start.
2. Node kirim webhook `qr` → status `qr` (UI polling `/sessions/{id}/status`).
3. Scan → webhook `connected` (+nomor) → status `connected`.
4. Pesan masuk → webhook `message` → `_handle_incoming`: tentukan owner percakapan,
   simpan ke inbox, cek auto-reply tim → balas.
5. Broadcast: task `dispatch-broadcasts` (tiap menit) jalankan yang `scheduled` & jatuh tempo;
   broadcast langsung dijalankan di thread scheduler dengan jeda antar nomor. Regular →
   `pending_approval` sampai supervisor/admin approve.

`WaService` bicara ke Node lewat `services/wa_gateway_client.py` (header `X-Internal-Token`).

---

## Database & migrasi

**Konfigurasi terpusat di `.env` root** (bukan `backend/.env` saat pakai Docker). Ganti DB
= edit `COMPOSE_PROFILES` + `DATABASE_URL`:

| Mode | COMPOSE_PROFILES | DATABASE_URL |
|---|---|---|
| Postgres lokal (Docker) | `localdb` | `postgresql+psycopg://wa_user:wa_password@db:5432/wa_gateway` |
| Supabase | *(kosong)* | URI Session pooler + `?sslmode=require` |
| Postgres host | *(kosong)* | `...@host.docker.internal:5432/...` |

- Compose menyuntik `DATABASE_URL` ke backend lewat `environment:` (override `backend/.env`).
- Service `db` (Postgres 16) hanya jalan kalau profil `localdb` aktif → untuk Supabase,
  kosongkan `COMPOSE_PROFILES` dan service lokal tidak ikut jalan.
- Startup (`main.py`): `wait_for_db` (retry sampai DB siap — penting saat Postgres warming up
  / koneksi Supabase) → `create_all` (buat tabel baru) → `run_light_migrations` (tambah kolom
  hilang via `ALTER TABLE ADD COLUMN`, idempotent) → **bootstrap admin** (promosikan user id
  terkecil jadi admin kalau belum ada).
- Engine (`db/session.py`): `pool_pre_ping=True` + `pool_recycle=1800` untuk DB cloud
  (Supabase memutus koneksi idle).
- **Ini bukan Alembic.** Production: pakai Alembic (skema versioned), hapus `create_all`/`migrate.py`.
- Inspeksi DB lokal: `psql -h localhost -p 5433 -U wa_user -d wa_gateway` (port host 5433,
  atur via `POSTGRES_HOST_PORT`).

---

## Konfigurasi (`backend/.env`)

| Var | Default | Catatan |
|---|---|---|
| `SECRET_KEY` | — (wajib) | `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | |
| `CORS_ORIGINS` | localhost:5173 | koma-separated |
| `DATABASE_URL` | — | **di Docker diambil dari `.env` root** (Postgres/Supabase) |
| `COOKIE_SECURE` / `COOKIE_SAMESITE` | false / lax | prod: `true` + HTTPS |
| `RATE_LIMIT_AUTH` / `_DEFAULT` | 5/menit · 100/menit | slowapi |
| `WA_GATEWAY_URL` | http://wa-gateway:3001 | alamat Node |
| `WA_INTERNAL_TOKEN` | change-me | **samakan dgn wa-gateway** |
| `WEBHOOK_SECRET` | change-me | **samakan dgn wa-gateway** |
| `SCHEDULER_TIMEZONE` | Asia/Jakarta | |
| `GOOGLE_CHAT_WEBHOOK` | "" | alert job gagal (opsional) |

---

## Menambah fitur baru (pola berlapis)

`models/x.py` → `schemas/x.py` → `repositories/x_repository.py` (sertakan varian
`list_scoped(ids)`) → `services/x_service.py` (pakai `scope.py`) → `endpoints/x.py`
(pasang guard yang sesuai) → daftarkan di `router.py`.

## Testing

`backend/tests/` (pytest). Service bisa di-test tanpa DB nyata (mock repo). Verifikasi RBAC
end-to-end paling cepat lewat API (login tiap role, cek visibilitas & guard).
