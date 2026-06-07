from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from ..models import gen_id


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, default=gen_id)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    order_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("orders.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    balance_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    balance_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    hold_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    hold_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="RUB")
    type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="completed")
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_system: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
