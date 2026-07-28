import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class GenerationBatch(Base):
    __tablename__ = "generation_batches"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    style: Mapped[str] = mapped_column(String(32), nullable=False)
    aspect_preset: Mapped[str] = mapped_column(String(32), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(64), nullable=True)
    negative_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    total_cost_credits: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=_now)

    tasks: Mapped[list["GenerationTask"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    batch_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("generation_batches.id"), nullable=False
    )
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    kie_task_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    # pending -> running -> done | failed | timeout

    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cost_credits: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=_now)
    updated_at: Mapped[datetime] = mapped_column(default=_now, onupdate=_now)

    batch: Mapped["GenerationBatch"] = relationship(back_populates="tasks")
