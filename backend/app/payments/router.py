from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.payments.cryptobot import CryptoBotAPI, CryptoBotError
from app.payments.service import PaymentService, InsufficientBalanceError

router = APIRouter(tags=["payments"])


class DepositRequest(BaseModel):
    amount: float = Field(..., gt=0)


class CheckPaymentRequest(BaseModel):
    invoice_id: int


class WithdrawRequest(BaseModel):
    amount: float = Field(..., gt=0)


@router.get("/payments/methods")
async def payment_methods():
    return [
        {"id": "cryptobot", "label": "CryptoBot", "desc": "USDT (крипта/Peer-to-Peer)", "active": True},
        {"id": "kassy", "label": "Kassy.ai", "desc": "Карты РФ, СБП", "active": bool(settings.kassy_api_key)},
        {"id": "platega", "label": "Platega", "desc": "СБП по РФ", "active": bool(settings.platega_api_key)},
    ]


@router.post("/payments/deposit")
async def create_deposit(
    body: DepositRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cryptobot = CryptoBotAPI(settings.cryptobot_api_key, settings.cryptobot_api_url)
    service = PaymentService(db, cryptobot)
    try:
        result = await service.create_deposit_invoice(
            user=user, amount=body.amount
        )
        await db.commit()
    except CryptoBotError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CryptoBot error: {e}",
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment error: {e}",
        )

    return result


@router.post("/payments/check")
async def check_payment(
    body: CheckPaymentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cryptobot = CryptoBotAPI(settings.cryptobot_api_key, settings.cryptobot_api_url)
    service = PaymentService(db, cryptobot)
    result = await service.check_invoice(body.invoice_id, user.id)
    await db.commit()
    return result


@router.post("/payments/withdraw")
async def create_withdrawal(
    body: WithdrawRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.amount < settings.min_withdraw_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum withdraw amount: {settings.min_withdraw_amount} RUB",
        )

    cryptobot = CryptoBotAPI(settings.cryptobot_api_key, settings.cryptobot_api_url)
    service = PaymentService(db, cryptobot)
    try:
        withdrawal = await service.process_withdraw(
            user=user, amount=body.amount
        )
        await db.commit()
    except InsufficientBalanceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except CryptoBotError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transfer failed: {e}",
        )

    return {
        "withdrawal_id": withdrawal.id,
        "status": withdrawal.status,
    }
