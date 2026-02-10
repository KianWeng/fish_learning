from datetime import datetime
from sqlalchemy import String, Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# 默认每用户存储上限 50MB（初始免费容量）
DEFAULT_STORAGE_LIMIT_BYTES = 50 * 1024 * 1024


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    unionid: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    nickname: Mapped[str | None] = mapped_column(String(128), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    storage_limit_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=DEFAULT_STORAGE_LIMIT_BYTES)
    storage_used_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
