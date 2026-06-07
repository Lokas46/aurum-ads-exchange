from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from ..models import gen_id


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, default=gen_id)
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chat_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    invite_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    subscribers_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_er: Mapped[float | None] = mapped_column(Float, nullable=True)
    categories: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price_per_post: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_per_hold: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_moderated: Mapped[bool] = mapped_column(Boolean, default=False)
    moderator_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    moderation_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    bot_added: Mapped[bool] = mapped_column(Boolean, default=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
