from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth.deps import get_current_user, require_admin
from ..models.user import User

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    first_name: str | None = None
    username: str | None = None


@router.get("/me")
async def get_my_profile(
    user: User = Depends(get_current_user),
):
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


@router.patch("/me")
async def update_my_profile(
    data: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.first_name:
        user.first_name = data.first_name
    if data.username:
        user.username = data.username
    await db.commit()
    return {"ok": True}


@router.get("/{user_id}/profile")
async def get_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"ok": False, "error": "User not found"}
    return {
        "ok": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "balance_rub": user.balance_rub,
            "role": user.role,
        },
    }


@router.get("/{user_id}/balance")
async def get_balance(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return {"balance": user.balance_rub if user else 0}
