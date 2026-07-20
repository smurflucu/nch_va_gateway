"""Aturan visibilitas data antar-role (RBAC + isolasi antar-tim).

Hirarki: admin > supervisor > regular user.
- admin      : lihat & kelola SEMUA data. Satu-satunya yang boleh input nomor WA.
- supervisor : lihat data timnya (dirinya + regular user di bawahnya). Antar
               supervisor TIDAK saling lihat.
- regular    : lihat inbox/broadcast miliknya sendiri; kontak & template tim
               (read-only); butuh approval untuk menjalankan broadcast.

"Tim" diidentifikasi oleh id supervisor pemiliknya (team owner).
"""
from sqlalchemy.orm import Session
from app.models.user import User, ROLE_ADMIN, ROLE_SUPERVISOR


def team_owner_id(user: User) -> int | None:
    """Id supervisor pemilik tim si user. None untuk admin (lintas-tim)."""
    if user.role == ROLE_ADMIN:
        return None
    if user.role == ROLE_SUPERVISOR:
        return user.id
    return user.supervisor_id  # regular user


def team_member_ids(db: Session, owner_id: int) -> list[int]:
    """Semua user_id dalam satu tim: supervisor + regular user di bawahnya."""
    rows = db.query(User.id).filter(User.supervisor_id == owner_id).all()
    return [owner_id] + [r[0] for r in rows]


def visible_user_ids(db: Session, user: User) -> list[int] | None:
    """user_id yang boleh DILIHAT oleh `user`.

    None = tanpa batas (admin). Dipakai untuk data yang di-scope per pembuat
    (mis. inbox, broadcast). Regular user hanya lihat miliknya sendiri.
    """
    if user.role == ROLE_ADMIN:
        return None
    if user.role == ROLE_SUPERVISOR:
        return team_member_ids(db, user.id)
    return [user.id]  # regular: dirinya saja


def team_scope_ids(db: Session, user: User) -> list[int] | None:
    """user_id level-TIM (kontak/template/sesi). None = semua (admin).

    Beda dengan visible_user_ids: di sini regular user ikut melihat data
    seluruh timnya (kontak & template dikelola supervisor), bukan cuma miliknya.
    """
    if user.role == ROLE_ADMIN:
        return None
    owner = team_owner_id(user)
    if owner is None:
        return [user.id]
    return team_member_ids(db, owner)
