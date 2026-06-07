import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models.user import User

router = APIRouter(tags=["auth"])


class TelegramLoginRequest(BaseModel):
    id: int
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    photo_url: str = ""
    auth_date: int = 0
    hash: str = ""


def validate_telegram_widget(data: dict, bot_token: str) -> bool:
    items = sorted((k, v) for k, v in data.items() if k != "hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in items)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, data.get("hash", ""))


@router.post("/auth/tg-login")
async def telegram_login(body: TelegramLoginRequest, db: AsyncSession = Depends(get_db)):
    widget_data = {
        "id": str(body.id),
        "first_name": body.first_name,
        "last_name": body.last_name,
        "username": body.username,
        "photo_url": body.photo_url,
        "auth_date": str(body.auth_date),
        "hash": body.hash,
    }
    if not validate_telegram_widget(widget_data, settings.bot_token):
        raise HTTPException(status_code=403, detail="Auth failed: invalid hash")

    telegram_id = body.id
    result = await db.execute(select(User).where(User.id == telegram_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=telegram_id,
            username=body.username or None,
            first_name=body.first_name or None,
            last_name=body.last_name or None,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    if not user.is_admin and telegram_id in settings.admin_ids:
        user.is_admin = True
        await db.flush()

    await db.commit()

    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "balance_rub": user.balance_rub,
        "hold_balance_rub": user.hold_balance_rub,
        "role": user.role,
        "is_admin": user.is_admin,
        "is_onboarded": user.is_onboarded,
    }


@router.get("/auth/dev-login")
async def dev_login(user_id: int, db: AsyncSession = Depends(get_db)):
    if not settings.debug:
        raise HTTPException(status_code=404)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=user_id, first_name=f"Dev#{user_id}")
        db.add(user)
        await db.flush()
        await db.refresh(user)
    if not user.is_admin and user_id in settings.admin_ids:
        user.is_admin = True
        await db.flush()
    await db.commit()
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "balance_rub": user.balance_rub,
        "hold_balance_rub": user.hold_balance_rub,
        "role": user.role,
        "is_admin": user.is_admin,
        "is_onboarded": user.is_onboarded,
    }
