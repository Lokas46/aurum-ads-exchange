import logging
import time
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models.user import User
from ..models.transaction import Transaction
from .. import cryptobot

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/methods")
async def payment_methods():
    return [
        {"id": "cryptobot", "label": "CryptoBot", "desc": "USDT (любая крипта)", "active": True},
        {"id": "platega", "label": "Platega", "desc": "СБП по РФ", "active": False},
        {"id": "kassa", "label": "Kassa.ai", "desc": "Карты РФ, СБП", "active": False},
    ]


class DepositRequest(BaseModel):
    user_id: int
    amount: float


class WithdrawRequest(BaseModel):
    user_id: int
    amount: float
    cryptobot_user_id: int


@router.post("/deposit")
async def create_deposit(req: DepositRequest):
    invoice = await cryptobot.create_invoice(
        amount=req.amount,
        description=f"Пополнение баланса #{req.user_id}",
        payload=f"deposit_{req.user_id}",
    )
    if invoice and invoice.get("bot_invoice_url"):
        return {"url": invoice["bot_invoice_url"], "amount": req.amount}
    return {"url": None, "amount": req.amount, "type": "mock"}


@router.post("/check")
async def check_payment(req: DepositRequest, db: AsyncSession = Depends(get_db)):
    logger.info("Checking payment for user %s", req.user_id)
    try:
        invoices = await cryptobot.get_invoices(status="paid", limit=50)
    except Exception as e:
        logger.error("get_invoices failed: %s", e, exc_info=True)
        return {"paid": False, "error": str(e)}
    if not invoices:
        logger.info("No paid invoices found")
        return {"paid": False}
    found = False
    for inv in invoices:
        payload = inv.get("payload", "")
        if payload == f"deposit_{req.user_id}":
            found = True
            usdt = float(inv.get("amount", 0))
            rub = round(usdt * settings.cryptobot_usdt_rate, 2)
            invoice_id = inv.get("invoice_id")
            tx_check = await db.execute(
                select(Transaction).where(Transaction.external_id == str(invoice_id))
            )
            if tx_check.scalar_one_or_none():
                continue
            result = await db.execute(select(User).where(User.id == req.user_id))
            user = result.scalar_one_or_none()
            if user:
                user.balance_rub += rub
                tx = Transaction(
                    user_id=req.user_id,
                    amount=rub,
                    type="deposit",
                    status="completed",
                    external_id=str(invoice_id),
                    description=f"Пополнение {rub} ₽ ({usdt} USDT) через CryptoBot",
                )
                db.add(tx)
                await db.commit()
            return {"paid": True, "amount_usdt": usdt, "amount_rub": rub}
    if found:
        return {"paid": True, "already_processed": True, "amount_usdt": 0, "amount_rub": 0}
    return {"paid": False}


@router.post("/withdraw")
async def withdraw(req: WithdrawRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == req.user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"ok": False, "error": "User not found"}
    await db.refresh(user)
    if user.balance_rub < req.amount:
        return {"ok": False, "error": "Недостаточно средств"}

    usdt_amount = round(req.amount / settings.cryptobot_usdt_rate, 2)
    spend_id = f"withdraw_{req.user_id}_{int(time.time())}"

    tx = Transaction(
        user_id=req.user_id,
        amount=req.amount,
        type="withdraw",
        status="pending",
        external_id=spend_id,
        description=f"Вывод {req.amount} ₽ → CryptoBot #{req.cryptobot_user_id}",
    )
    db.add(tx)
    await db.flush()

    transfer = await cryptobot.transfer(req.cryptobot_user_id, usdt_amount, spend_id)
    if transfer and transfer.get("ok"):
        tx.status = "completed"
        user.balance_rub -= req.amount
        await db.commit()
        return {"ok": True, "amount": req.amount}

    tx.status = "failed"
    await db.commit()
    return {"ok": False, "error": "Ошибка вывода"}
