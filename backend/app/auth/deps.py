import logging

from fastapi import Header, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.telegram import validate_init_data, InvalidInitDataError, ExpiredInitDataError
from app.database import get_db
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)


async def _resolve_user(telegram_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=telegram_id, first_name=f"User#{telegram_id}")
        db.add(user)
        await db.flush()
        await db.refresh(user)
    if not user.is_admin and telegram_id in settings.admin_ids:
        user.is_admin = True
        await db.flush()
    return user


async def get_current_user(
    authorization: str | None = Header(None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> User:
    dev_id = request.headers.get("X-Dev-User-Id") or (request.query_params.get("__dev_user_id") if request else None)

    # Dev/id fallback (works even when initData is present but invalid)
    if settings.debug and dev_id:
        return await _resolve_user(int(dev_id), db)

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Telegram-Init-Data header",
        )

    try:
        data = validate_init_data(
            authorization,
            settings.bot_token,
            settings.init_data_expiration,
        )
    except (InvalidInitDataError, ExpiredInitDataError) as e:
        logger.warning("Init data validation failed: %s", e)
        if settings.debug and dev_id:
            return await _resolve_user(int(dev_id), db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    telegram_user = data["user"]
    telegram_id = telegram_user["id"]

    result = await db.execute(
        select(User).where(User.id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=telegram_id,
            username=telegram_user.get("username"),
            first_name=telegram_user.get("first_name"),
            last_name=telegram_user.get("last_name"),
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    if not user.is_admin and telegram_id in settings.admin_ids:
        user.is_admin = True
        await db.flush()

    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
