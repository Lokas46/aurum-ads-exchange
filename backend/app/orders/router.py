from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.order import Order
from app.models.channel import Channel
from app.orders.service import OrderService, InsufficientBalanceError, InvalidOrderStateError

router = APIRouter(tags=["orders"])


class CreateOrderRequest(BaseModel):
    channel_id: int
    post_text: str = Field(..., min_length=1, max_length=4000)


class OrderResponse(BaseModel):
    id: int
    channel_id: int
    amount: float
    status: str
    post_text: str | None


@router.post("/orders")
async def create_order(
    body: CreateOrderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    channel_result = await db.execute(
        select(Channel).where(Channel.id == body.channel_id)
    )
    channel = channel_result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    if not channel.is_active or not channel.is_moderated:
        raise HTTPException(status_code=400, detail="Channel is not available")
    if not channel.price_per_post:
        raise HTTPException(status_code=400, detail="Channel has no price set")

    service = OrderService(db)
    try:
        order = await service.create_order(
            advertiser_id=user.id,
            channel_id=channel.id,
            channel_owner_id=channel.owner_id,
            channel_name=channel.title,
            post_text=body.post_text,
            amount=channel.price_per_post,
        )
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return OrderResponse(
        id=order.id,
        channel_id=order.channel_id,
        amount=order.amount,
        status=order.status,
        post_text=order.post_text,
    )


@router.get("/orders")
async def list_orders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(
            (Order.advertiser_id == user.id) | (Order.channel_owner_id == user.id)
        ).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return [
        OrderResponse(
            id=o.id,
            channel_id=o.channel_id,
            amount=o.amount,
            status=o.status,
            post_text=o.post_text,
        )
        for o in orders
    ]


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.advertiser_id != user.id and order.channel_owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    return OrderResponse(
        id=order.id,
        channel_id=order.channel_id,
        amount=order.amount,
        status=order.status,
        post_text=order.post_text,
    )


@router.post("/orders/{order_id}/approve")
async def approve_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.channel_owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Only channel owner can approve")

    try:
        order = await service.approve_order(order_id)
        await db.commit()
    except InvalidOrderStateError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": order.status, "id": order.id}


@router.post("/orders/{order_id}/reject")
async def reject_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.channel_owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Only channel owner can reject")

    try:
        order = await service.reject_order(order_id)
        await db.commit()
    except InvalidOrderStateError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": order.status, "id": order.id}


@router.post("/orders/{order_id}/confirm")
async def confirm_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.advertiser_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Only advertiser can confirm")

    try:
        order = await service.confirm_order(order_id)
        await db.commit()
    except InvalidOrderStateError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": order.status, "id": order.id}
