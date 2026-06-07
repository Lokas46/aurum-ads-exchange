from decimal import Decimal
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.order import Order
from app.models.user import User
from app.models.transaction import Transaction


class InsufficientBalanceError(Exception):
    pass


class InvalidOrderStateError(Exception):
    pass


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(
        self,
        advertiser_id: int,
        channel_id: int,
        channel_owner_id: int,
        channel_name: str,
        post_text: str,
        amount: float,
    ) -> Order:
        user_result = await self.db.execute(
            select(User).where(User.id == advertiser_id).with_for_update()
        )
        advertiser = user_result.scalar_one_or_none()
        if not advertiser:
            raise InsufficientBalanceError("Advertiser not found")

        if advertiser.balance_rub < amount:
            raise InsufficientBalanceError(
                f"Insufficient balance: {advertiser.balance_rub} < {amount}"
            )

        commission_rate = Decimal(str(settings.commission_rate))
        commission = float((Decimal(str(amount)) * commission_rate).quantize(Decimal("0.01")))
        owner_amount = amount - commission

        deadline = datetime.now(timezone.utc) + timedelta(seconds=settings.order_approval_timeout)

        order = Order(
            advertiser_id=advertiser_id,
            channel_id=channel_id,
            channel_owner_id=channel_owner_id,
            channel_name=channel_name,
            amount=amount,
            commission=commission,
            commission_rate=settings.commission_rate,
            owner_amount=owner_amount,
            post_text=post_text,
            status="pending",
            deadline=deadline,
        )
        self.db.add(order)
        await self.db.flush()

        advertiser.balance_rub -= amount
        advertiser.hold_balance_rub += amount

        self.db.add(Transaction(
            user_id=advertiser_id,
            amount=-amount,
            type="hold",
            status="completed",
            description=f"Order #{order.id}: hold {amount} RUB",
        ))

        return order

    async def approve_order(self, order_id: int) -> Order:
        order_result = await self.db.execute(
            select(Order).where(Order.id == order_id).with_for_update()
        )
        order = order_result.scalar_one_or_none()
        if not order:
            raise InvalidOrderStateError("Order not found")

        if order.status != "pending":
            raise InvalidOrderStateError(f"Cannot approve order in status: {order.status}")

        advertiser_result = await self.db.execute(
            select(User).where(User.id == order.advertiser_id).with_for_update()
        )
        advertiser = advertiser_result.scalar_one_or_none()

        owner_result = await self.db.execute(
            select(User).where(User.id == order.channel_owner_id).with_for_update()
        )
        owner = owner_result.scalar_one_or_none()

        advertiser.hold_balance_rub -= order.amount
        owner.balance_rub += order.owner_amount

        self.db.add(Transaction(
            user_id=order.channel_owner_id,
            amount=order.owner_amount,
            type="release",
            status="completed",
            description=f"Order #{order.id}: release {order.owner_amount} RUB",
        ))

        platform_user = await self.db.execute(
            select(User).where(User.id == settings.platform_user_id).with_for_update()
        )
        platform = platform_user.scalar_one_or_none()
        if platform:
            platform.balance_rub += order.commission

        self.db.add(Transaction(
            user_id=settings.platform_user_id,
            amount=order.commission,
            type="commission",
            status="completed",
            description=f"Order #{order.id}: commission {order.commission} RUB",
        ))

        order.status = "active"

        return order

    async def reject_order(self, order_id: int) -> Order:
        order_result = await self.db.execute(
            select(Order).where(Order.id == order_id).with_for_update()
        )
        order = order_result.scalar_one_or_none()
        if not order:
            raise InvalidOrderStateError("Order not found")

        if order.status not in ("pending",):
            raise InvalidOrderStateError(f"Cannot reject order in status: {order.status}")

        advertiser_result = await self.db.execute(
            select(User).where(User.id == order.advertiser_id).with_for_update()
        )
        advertiser = advertiser_result.scalar_one_or_none()
        if not advertiser:
            raise InvalidOrderStateError("Advertiser not found")

        advertiser.hold_balance_rub -= order.amount
        advertiser.balance_rub += order.amount

        self.db.add(Transaction(
            user_id=order.advertiser_id,
            amount=order.amount,
            type="refund",
            status="completed",
            description=f"Order #{order.id}: refund {order.amount} RUB",
        ))

        order.status = "cancelled"

        return order

    async def confirm_order(self, order_id: int) -> Order:
        order_result = await self.db.execute(
            select(Order).where(Order.id == order_id).with_for_update()
        )
        order = order_result.scalar_one_or_none()
        if not order:
            raise InvalidOrderStateError("Order not found")

        if order.status != "active":
            raise InvalidOrderStateError(f"Cannot confirm order in status: {order.status}")

        order.status = "completed"
        order.is_confirmed = True
        order.confirmed_at = datetime.now(timezone.utc)

        return order

    async def get_order(self, order_id: int) -> Order | None:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
