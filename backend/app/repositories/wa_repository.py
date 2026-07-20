"""Repository untuk semua entitas WA. Semua query WAJIB di-filter user_id
supaya data antar-user tidak bocor (multi-tenant)."""
from sqlalchemy.orm import Session
from app.models.wa import (
    WaSession, Contact, MessageTemplate, Message, AutoReply, ApiKey, Broadcast,
)
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[WaSession]):
    def __init__(self, db: Session):
        super().__init__(WaSession, db)

    def list_for_team(self, team_owner_id: int | None) -> list[WaSession]:
        """Nomor milik satu tim (supervisor_id = team_owner_id). None = semua (admin)."""
        q = self.db.query(WaSession)
        if team_owner_id is not None:
            q = q.filter(WaSession.supervisor_id == team_owner_id)
        return q.order_by(WaSession.created_at.desc()).all()

    def get_for_team(self, session_id: int, team_owner_id: int | None) -> WaSession | None:
        q = self.db.query(WaSession).filter(WaSession.id == session_id)
        if team_owner_id is not None:
            q = q.filter(WaSession.supervisor_id == team_owner_id)
        return q.first()

    def get_by_key(self, session_key: str) -> WaSession | None:
        return self.db.query(WaSession).filter(WaSession.session_key == session_key).first()


class ContactRepository(BaseRepository[Contact]):
    def __init__(self, db: Session):
        super().__init__(Contact, db)

    def list_scoped(self, user_ids: list[int] | None) -> list[Contact]:
        """Kontak level-tim. user_ids = anggota tim; None = semua (admin)."""
        q = self.db.query(Contact)
        if user_ids is not None:
            q = q.filter(Contact.user_id.in_(user_ids))
        return q.order_by(Contact.name).all()

    def get_scoped(self, cid: int, user_ids: list[int] | None) -> Contact | None:
        q = self.db.query(Contact).filter(Contact.id == cid)
        if user_ids is not None:
            q = q.filter(Contact.user_id.in_(user_ids))
        return q.first()

    def find_by_phone_scoped(self, user_ids: list[int] | None, phone: str) -> Contact | None:
        q = self.db.query(Contact).filter(Contact.phone == phone)
        if user_ids is not None:
            q = q.filter(Contact.user_id.in_(user_ids))
        return q.first()


class TemplateRepository(BaseRepository[MessageTemplate]):
    def __init__(self, db: Session):
        super().__init__(MessageTemplate, db)

    def list_scoped(self, user_ids: list[int] | None) -> list[MessageTemplate]:
        q = self.db.query(MessageTemplate)
        if user_ids is not None:
            q = q.filter(MessageTemplate.user_id.in_(user_ids))
        return q.order_by(MessageTemplate.name).all()

    def get_scoped(self, tid: int, user_ids: list[int] | None) -> MessageTemplate | None:
        q = self.db.query(MessageTemplate).filter(MessageTemplate.id == tid)
        if user_ids is not None:
            q = q.filter(MessageTemplate.user_id.in_(user_ids))
        return q.first()


class MessageRepository(BaseRepository[Message]):
    def __init__(self, db: Session):
        super().__init__(Message, db)

    def list_scoped(
        self, user_ids: list[int] | None, direction: str | None = None, limit: int = 100
    ) -> list[Message]:
        """Inbox/outbox. user_ids sesuai visibilitas: admin=None(all),
        supervisor=anggota tim, regular=[dirinya]. """
        q = self.db.query(Message)
        if user_ids is not None:
            q = q.filter(Message.user_id.in_(user_ids))
        if direction:
            q = q.filter(Message.direction == direction)
        return q.order_by(Message.created_at.desc()).limit(limit).all()

    def last_conversation_owner(self, session_id: int, chat_number: str) -> int | None:
        """Siapa (user_id) yang terakhir MENGIRIM ke nomor ini di sesi ini.
        Dipakai untuk 'memiliki' percakapan → regular lihat inbox balasannya."""
        row = (
            self.db.query(Message.user_id)
            .filter(
                Message.session_id == session_id,
                Message.chat_number == chat_number,
                Message.direction == "out",
            )
            .order_by(Message.created_at.desc())
            .first()
        )
        return row[0] if row else None


class AutoReplyRepository(BaseRepository[AutoReply]):
    def __init__(self, db: Session):
        super().__init__(AutoReply, db)

    def list_scoped(self, user_ids: list[int] | None) -> list[AutoReply]:
        q = self.db.query(AutoReply)
        if user_ids is not None:
            q = q.filter(AutoReply.user_id.in_(user_ids))
        return q.order_by(AutoReply.created_at.desc()).all()

    def get_scoped(self, rid: int, user_ids: list[int] | None) -> AutoReply | None:
        q = self.db.query(AutoReply).filter(AutoReply.id == rid)
        if user_ids is not None:
            q = q.filter(AutoReply.user_id.in_(user_ids))
        return q.first()

    def list_enabled(self, user_ids: list[int], session_id: int) -> list[AutoReply]:
        """Aturan aktif untuk sesi ini, milik tim pemilik sesi."""
        return self.db.query(AutoReply).filter(
            AutoReply.user_id.in_(user_ids),
            AutoReply.enabled.is_(True),
            (AutoReply.session_id == session_id) | (AutoReply.session_id.is_(None)),
        ).all()


class ApiKeyRepository(BaseRepository[ApiKey]):
    def __init__(self, db: Session):
        super().__init__(ApiKey, db)

    def list_for_user(self, user_id: int) -> list[ApiKey]:
        return self.db.query(ApiKey).filter(ApiKey.user_id == user_id).all()

    def get_owned(self, kid: int, user_id: int) -> ApiKey | None:
        return self.db.query(ApiKey).filter(ApiKey.id == kid, ApiKey.user_id == user_id).first()

    def list_by_prefix(self, prefix: str) -> list[ApiKey]:
        return self.db.query(ApiKey).filter(
            ApiKey.prefix == prefix, ApiKey.enabled.is_(True)
        ).all()


class BroadcastRepository(BaseRepository[Broadcast]):
    def __init__(self, db: Session):
        super().__init__(Broadcast, db)

    def list_scoped(self, user_ids: list[int] | None) -> list[Broadcast]:
        """admin=None(all), supervisor=anggota tim, regular=[dirinya]."""
        q = self.db.query(Broadcast)
        if user_ids is not None:
            q = q.filter(Broadcast.user_id.in_(user_ids))
        return q.order_by(Broadcast.created_at.desc()).all()

    def get_scoped(self, bid: int, user_ids: list[int] | None) -> Broadcast | None:
        q = self.db.query(Broadcast).filter(Broadcast.id == bid)
        if user_ids is not None:
            q = q.filter(Broadcast.user_id.in_(user_ids))
        return q.first()

    def list_pending_for_team(self, team_ids: list[int] | None) -> list[Broadcast]:
        """Antrian broadcast menunggu approval (dibuat regular user)."""
        q = self.db.query(Broadcast).filter(Broadcast.status == "pending_approval")
        if team_ids is not None:
            q = q.filter(Broadcast.user_id.in_(team_ids))
        return q.order_by(Broadcast.created_at.desc()).all()

    def list_due(self, now) -> list[Broadcast]:
        return self.db.query(Broadcast).filter(
            Broadcast.status == "scheduled", Broadcast.scheduled_at <= now
        ).all()
