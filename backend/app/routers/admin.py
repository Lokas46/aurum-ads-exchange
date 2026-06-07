from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..auth.deps import require_admin
from ..models.user import User
from ..models.channel import Channel
from ..models.order import Order
from ..models.withdraw_request import WithdrawRequest
from ..payments.cryptobot import CryptoBotAPI

router = APIRouter()


@router.get("/dashboard")
async def dashboard(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    users_count = (await db.execute(select(User))).scalars().all()
    channels_count = (await db.execute(select(Channel))).scalars().all()
    orders_count = (await db.execute(select(Order))).scalars().all()

    return {
        "users": len(users_count),
        "channels": len(channels_count),
        "orders": len(orders_count),
        "pending_channels": len([c for c in channels_count if not c.is_moderated]),
        "active_channels": len([c for c in channels_count if c.is_active]),
        "pending_orders": len([o for o in orders_count if o.status == "pending"]),
        "active_orders": len([o for o in orders_count if o.status == "active"]),
    }


@router.get("/cryptobot-setup")
async def setup_cryptobot(admin: User = Depends(require_admin)):
    base = settings.webhook_base_url or settings.api_base_url
    webhook_url = base.rstrip("/") + "/api/webhooks/cryptobot"
    return {
        "ok": True,
        "webhook_url": webhook_url,
    }


@router.get("/cryptobot-balance")
async def cryptobot_balance(admin: User = Depends(require_admin)):
    api = CryptoBotAPI(settings.cryptobot_api_key, settings.cryptobot_api_url)
    try:
        balance = await api.get_balance()
        return {"balance": balance}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/withdraw-requests")
async def withdraw_requests(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WithdrawRequest).order_by(WithdrawRequest.created_at.desc())
    )
    requests = result.scalars().all()
    return [
        {
            "id": wr.id,
            "user_id": wr.user_id,
            "amount": wr.amount,
            "fee": wr.fee,
            "net_amount": wr.net_amount,
            "status": wr.status,
            "created_at": wr.created_at.isoformat() if wr.created_at else None,
        }
        for wr in requests
    ]
