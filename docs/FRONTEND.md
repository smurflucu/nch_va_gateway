# Frontend — Technical Reference

React 18 + Vite SPA, arsitektur **feature-based**. State ringan (zustand), styling lewat
**CSS design tokens** (bukan Tailwind). Tema light ala dashboard modern.

## Stack

- **React 18** + **Vite 6**
- **react-router-dom 6** — routing
- **zustand** — state (auth)
- **axios** — HTTP + interceptor auto-refresh
- **CSS variables** di `src/index.css` — design system (tanpa framework CSS)

Alias `@` → `src/` (lihat `vite.config.js`). Build: `npm run build` (di Docker → di-serve nginx).

## Struktur

```
src/
  main.jsx, App.jsx           # entry + definisi route (+ role guard)
  index.css                   # ⭐ design tokens + utility class + primitive style
  config/
    routes.js                 # peta path
    constants.js              # APP_NAME
  services/api.js             # axios instance + interceptor refresh
  components/
    ui/                       # primitif: Button, Card, Badge, Input, Select, Textarea
    common/  Sidebar.jsx      # nav role-aware
             Navbar.jsx       # topbar (judul halaman + avatar)
  layouts/  MainLayout.jsx    # shell: Sidebar + Topbar + <Outlet>
            AuthLayout.jsx    # layout halaman login
  features/
    auth/                     # store + hooks (login/logout/restore) + LoginForm + api
    wa/                       # api + hooks (useSessions, useUsers, dll) + QRConnect
    jobs/                     # scheduler UI
  pages/                      # tipis: compose feature + primitif
  hooks/ lib/ utils/
```

Arah dependency: `features → components (ui/common)`. Pages tipis, hanya merangkai.

---

## Design system (`src/index.css`)

Semua warna dari **CSS variable** → ganti tema = ubah token, tidak sentuh komponen.

```css
--bg --surface --surface-2 --border --text --text-dim
--accent (--accent-soft) --success --warn --danger (+ *-soft)
--radius --radius-sm --shadow --sidebar-w --topbar-h
```

Utility class siap pakai: `.card .field .btn(.btn-primary/ghost/danger/success/-sm)
.table .list-item .row-between .grid-stats .avatar .role-chip .muted .page-head`.

Primitif (`components/ui/`) memakai variable/class ini, jadi mengubah token otomatis
merambat ke seluruh halaman:

| Primitif | Props penting |
|---|---|
| `Button` | `variant` (primary/ghost/danger/success), `size="sm"` |
| `Card` | `style`, `className` |
| `Badge` | anak = status (`connected`, `pending_approval`, `in/out`, …) → warna otomatis |
| `Input`/`Select`/`Textarea` | `label`, props native (pakai class `.field`, ada focus ring) |

Fokus/hover butuh CSS class (inline style tak bisa `:focus`), jadi ada di `index.css`.

---

## Auth & state

`features/auth/store/auth.store.js` (zustand): `{ user, accessToken, initialized }`.
Access token **hanya di memory** (tidak persist → aman XSS).

`features/auth/hooks/useAuth.js`:
- `login(email, pw)` → simpan token → `GET /users/me` → set `user` (termasuk `role`, `supervisor_id`).
- `useRestoreSession()` (dipanggil di `App`) → `POST /auth/refresh` pakai cookie saat load.
- `logout()`.

`services/api.js`: axios `withCredentials`, request interceptor pasang `Bearer`, response
interceptor tangani `401` → refresh sekali → ulangi request.

---

## Role-aware UI

`user.role` (`admin`/`supervisor`/`user`) menentukan tampilan.

- **Sidebar** (`components/common/Sidebar.jsx`): menu punya properti `roles`; item yang tak
  cocok disembunyikan (mis. `Tim & User` & `Auto-Reply` = admin/supervisor; `API Gateway` &
  `Jobs` = admin).
- **Route guard** (`App.jsx`): `ProtectedRoute` cek login; `roleGuard(el, roles)` redirect ke
  dashboard kalau role tak diizinkan. Guard UI ini **pelengkap**, bukan pengganti — otorisasi
  sebenarnya tetap di backend.
- **Per-halaman**: tombol/aksi dikondisikan `isAdmin` / `canApprove` (mis. input nomor di
  `SessionsPage`, antrian approval di `BroadcastPage`, edit/hapus user di `TeamPage`).

---

## Data fetching (`features/wa/hooks/useWa.js`)

Helper `useList(fetcher, { poll, enabled })` → `{ items, loading, error, refresh }`.
Hook siap pakai: `useSessions` (poll 5s), `useInbox`, `useContacts`, `useTemplates`,
`useBroadcasts`, `useAutoReplies`, `useApiKeys`, `useUsers`, `useSupervisors(enabled)`,
`usePendingBroadcasts(enabled)`.

- `enabled` mematikan fetch untuk endpoint yang di-gate role (hindari 401/403 berulang, mis.
  `useSupervisors(isAdmin)`).
- Setelah mutasi yang bisa mengubah **nama/daftar** (edit user, ganti role, assign), refresh
  **semua list terkait** — mis. `TeamPage` punya `reload()` yang me-refresh `users` **dan**
  `supervisors` agar dropdown tidak menampilkan nama lama.

API layer: `features/wa/services/wa.api.js` (semua call `/api/v1/...`).

---

## Halaman (`src/pages/`)

| Page | Route | Akses | Isi |
|---|---|---|---|
| Dashboard | `/dashboard` | semua | kartu statistik + status nomor + aktivitas |
| Nomor WA | `/sessions` | semua (input=admin) | list + QR + assign tim |
| Kirim Pesan | `/send` | semua | kirim satuan |
| Inbox | `/inbox` | semua (scoped) | pesan masuk/keluar |
| Broadcast | `/broadcast` | semua | buat + antrian approval (supervisor/admin) |
| Kontak / Template | `/contacts`, `/templates` | baca semua, tulis supervisor+ | — |
| Auto-Reply | `/auto-reply` | admin/supervisor | aturan kata kunci |
| Tim & User | `/team` | admin/supervisor | tabel + create + **edit modal** + hapus |
| API Gateway | `/api-keys` | admin | kelola API-key |
| Jobs | `/jobs` | admin | scheduler |

---

## Menambah halaman baru

1. Tambah path di `config/routes.js`.
2. Buat `pages/XPage.jsx` (rangkai primitif + hook dari `features/`).
3. Daftarkan route di `App.jsx` (`guard(...)` atau `roleGuard(..., [roles])`).
4. Tambah item menu di `components/common/Sidebar.jsx` (isi `roles` bila perlu).
5. Kalau butuh data: tambah call di `features/wa/services/wa.api.js` + hook di `hooks/useWa.js`.

## Styling — do & don't

- **Do**: pakai CSS variable & utility class; tambah warna/spacing baru sebagai token di
  `index.css`.
- **Don't**: hardcode warna hex di komponen (kecuali via token) — merusak konsistensi tema.
- Ikuti kepadatan/idiom komponen sekitar (banyak inline `style={{}}` yang mereferensikan
  `var(--...)`).
