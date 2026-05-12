from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Generator

from sqlalchemy import JSON, DateTime, Float, Integer, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

_DEFAULT_SQLITE = "sqlite:///./data/vegetal_alloys.db"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_SQLITE)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class VegetalAlloy(Base):
    __tablename__ = "vegetal_alloys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    source_crop: Mapped[str] = mapped_column(String(80))
    chemical_composition: Mapped[dict[str, Any]] = mapped_column(JSON)
    physical_properties: Mapped[dict[str, Any]] = mapped_column(JSON)
    sustainability_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=lambda: datetime.now(timezone.utc))
    witness_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)


def init_db() -> None:
    if DATABASE_URL.startswith("sqlite:///"):
        rel = DATABASE_URL.removeprefix("sqlite:///")
        if rel and not rel.startswith(":memory:"):
            abs_path = os.path.abspath(rel)
            parent = os.path.dirname(abs_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    if DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.commit()


def calculate_sustainability(composition: dict[str, Any]) -> float:
    cellulose = float(composition.get("cellulose", 0) or 0) / 100.0
    lignin = float(composition.get("lignin", 0) or 0) / 100.0
    return float(max(0.0, min(1.0, 0.7 * cellulose + 0.3 * lignin)))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
