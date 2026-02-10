"""存储扩容订单：用于微信支付下单与回调落单。"""
from datetime import datetime
from sqlalchemy import Integer, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StorageOrder(Base):
    __tablename__ = "storage_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    out_trade_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    add_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount_fen: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)  # pending | paid | failed | closed
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="storage_orders")
