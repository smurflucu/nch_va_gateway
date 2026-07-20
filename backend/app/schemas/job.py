from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class JobCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    task_name: str
    cron: str = Field(examples=["0 6 * * *"])
    description: str = Field(default="", max_length=255)
    enabled: bool = True


class JobUpdate(BaseModel):
    cron: str | None = None
    enabled: bool | None = None
    description: str | None = Field(default=None, max_length=255)


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    task_name: str
    cron: str
    enabled: bool
    description: str
    next_run: datetime | None = None  # diisi dari scheduler, bukan DB


class JobRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    job_id: int
    trigger: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    output: str
