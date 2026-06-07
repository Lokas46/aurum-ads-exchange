from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.order import Order

router = APIRouter()


class CreateOrderRequest(BaseModel):
    advertiser_id: int
    channel_id: int
    amount: float


@router.get("/")
async def list_orders(user_id: int | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Order)
    if user_id:
        query = query.where(
            (Order.advertiser_id == user_id)
        )
    query = query.order_by(Order.created_at.desc())
    result = await db.execute(query)
    orders = result.scalars().all()
    return [
        {
            "id": o.id,
            "advertiser_id": o.advertiser_id,
            "channel_id": o.channel_id,
            "amount": o.amount,
            "status": o.status,
            "post_text": o.post_text,
            "post_link": o.post_link,
            "is_confirmed": o.is_confirmed,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]


@router.post("/")
async def create_order(req: CreateOrderRequest, db: AsyncSession = Depends(get_db)):
    order = Order(
        advertiser_id=req.advertiser_id,
        channel_id=req.channel_id,
        amount=req.amount,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return {"id": order.id, "status": order.status}
