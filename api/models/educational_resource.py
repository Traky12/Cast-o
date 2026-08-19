from __future__ import annotations

try:
    from sqlalchemy import Column, DateTime, Integer, String, Text, func
except Exception:  # pragma: no cover
    Column = None
    DateTime = None
    Integer = None
    String = None
    Text = None
    func = None

try:
    from database.session import Base
except ModuleNotFoundError:  # pragma: no cover
    from api.database.session import Base


class EducationalResource(Base):
    __tablename__ = "educational_resources"
    __table_args__ = {"extend_existing": True}

    if Column is not None:
        id = Column(Integer, primary_key=True, index=True)
        content_hash = Column(String(128), nullable=False, index=True)
        audience = Column(String(32), nullable=False)
        topic = Column(String(128), nullable=False)
        content = Column(Text, nullable=False)
        blockchain_txid = Column(String(255), nullable=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)