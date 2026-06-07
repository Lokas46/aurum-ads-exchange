from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from ..models import gen_id


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, default=gen_id)
    advertiser_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("channels.id"), index=True)
    channel_owner_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    channel_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    commission: Mapped[float | None] = mapped_column(Float, nullable=True)
    commission_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    owner_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    post_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
