from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    role: str
    supervisor_id: int | None = None
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


# --- Manajemen user oleh admin / supervisor ---
class AdminUserCreate(BaseModel):
    """Admin membuat user baru dengan role apa pun.
    Untuk role 'user' (regular), supervisor_id wajib menunjuk ke supervisor."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)
    role: Literal["admin", "supervisor", "user"] = "user"
    supervisor_id: int | None = None


class SupervisorRegularCreate(BaseModel):
    """Supervisor membuat regular user untuk timnya sendiri (tanpa pilih supervisor)."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)


class UserAdminUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: Literal["admin", "supervisor", "user"] | None = None
    supervisor_id: int | None = None
    is_active: bool | None = None
