from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from ..models import gen_id


class PaymentInvoice(Base):
    __tablename__ = "payment_invoices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, default=gen_id)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    asset: Mapped[str] = mapped_column(String(20), default="USDT")
    crypto_bot_invoice_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    kassy_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platega_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    pay_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
