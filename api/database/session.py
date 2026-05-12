from __future__ import annotations

import os
from contextlib import suppress
from typing import Any, cast

try:
    from sqlalchemy import create_engine  # type: ignore[reportMissingImports]
    from sqlalchemy.orm import declarative_base, sessionmaker  # type: ignore[reportMissingImports]
except Exception:  # pragma: no cover
    create_engine = None
    declarative_base = None
    sessionmaker = None

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if declarative_base is not None:
    Base: Any = cast(Any, declarative_base())
else:  # pragma: no cover
    class _FallbackBase:
        metadata = None

    Base = _FallbackBase

engine: Any = None
SessionLocal: Any = None

if DATABASE_URL and create_engine is not None and sessionmaker is not None:
    engine = cast(Any, create_engine(DATABASE_URL, pool_pre_ping=True))
    SessionLocal = cast(Any, sessionmaker(bind=engine, autocommit=False, autoflush=False))


def init_db() -> None:
    metadata = getattr(Base, "metadata", None)
    if engine is None or metadata is None:
        return
    with suppress(Exception):
        metadata.create_all(bind=engine)