from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from ..models import gen_id


class WithdrawRequest(Base):
    __tablename__ = "withdraw_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, default=gen_id)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    net_amount: Mapped[float] = mapped_column(Float, default=0.0)
    asset: Mapped[str] = mapped_column(String(20), default="USDT")
    destination_type: Mapped[str] = mapped_column(String(30))
    destination_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    admin_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    crypto_bot_transfer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
