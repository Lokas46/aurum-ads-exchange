from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..auth.deps import get_current_user, require_admin
from ..models.user import User
from ..models.channel import Channel

router = APIRouter()


class CreateChannelRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    username: str | None = None
    description: str | None = None
    price_per_post: float | None = None
    categories: str | None = None


class ModerateRequest(BaseModel):
    approve: bool


@router.post("/")
async def create_channel(
    req: CreateChannelRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    channel = Channel(
        owner_id=user.id,
        title=req.title,
        username=req.username,
        description=req.description,
        price_per_post=req.price_per_post,
        categories=req.categories,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return {"id": channel.id, "ok": True}


@router.get("/")
async def list_channels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Channel)
        .where(Channel.is_active == True)
        .where(Channel.is_moderated == True)
        .order_by(Channel.subscribers_count.desc().nullslast())
    )
    channels = result.scalars().all()
    return [
        {
            "id": ch.id,
            "title": ch.title,
            "username": ch.username,
            "description": ch.description,
            "subscribers_count": ch.subscribers_count,
            "avg_views": ch.avg_views,
            "price_per_post": ch.price_per_post,
            "categories": ch.categories or "",
            "is_verified": ch.is_verified,
        }
        for ch in channels
    ]


@router.get("/my")
async def my_channels(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Channel).where(Channel.owner_id == user.id)
    )
    channels = result.scalars().all()
    return [
        {
            "id": ch.id,
            "title": ch.title,
            "username": ch.username,
            "subscribers_count": ch.subscribers_count,
            "price_per_post": ch.price_per_post,
            "is_moderated": ch.is_moderated,
            "is_active": ch.is_active,
        }
        for ch in channels
    ]


@router.get("/all")
async def all_channels(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Channel).order_by(Channel.created_at.desc()))
    channels = result.scalars().all()
    return [
        {
            "id": ch.id,
            "title": ch.title,
            "username": ch.username,
            "description": ch.description,
            "price_per_post": ch.price_per_post,
            "categories": ch.categories,
            "owner_id": ch.owner_id,
            "is_moderated": ch.is_moderated,
            "is_active": ch.is_active,
            "subscribers_count": ch.subscribers_count,
            "bot_added": ch.bot_added,
        }
        for ch in channels
    ]


@router.post("/{channel_id}/moderate")
async def moderate_channel(
    channel_id: int,
    req: ModerateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    ch.is_moderated = True
    ch.is_active = req.approve
    ch.moderator_id = admin.id
    await db.commit()
    return {"ok": True, "id": ch.id, "approved": req.approve}


@router.get("/{channel_id}")
async def get_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    return {
        "id": ch.id,
        "title": ch.title,
        "username": ch.username,
        "description": ch.description,
        "subscribers_count": ch.subscribers_count,
        "avg_views": ch.avg_views,
        "avg_er": ch.avg_er,
        "price_per_post": ch.price_per_post,
        "price_per_hold": ch.price_per_hold,
        "categories": ch.categories or "",
        "is_verified": ch.is_verified,
        "owner_id": ch.owner_id,
    }
