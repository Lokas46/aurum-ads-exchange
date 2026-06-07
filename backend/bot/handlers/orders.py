import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.database import async_session
from app.models.channel import Channel
from app.models.order import Order
from app.models.user import User
from app.orders.service import OrderService, InsufficientBalanceError, InvalidOrderStateError
from bot.keyboards.orders import order_keyboard, order_approve_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("create_order:"))
async def cb_create_order(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()
        if not channel:
            await callback.answer("❌ Канал не найден")
            return

        user_result = await session.execute(select(User).where(User.id == callback.from_user.id))
        user = user_result.scalar_one_or_none()
        if not user:
            await callback.answer("❌ Пользователь не найден. Используй /start", show_alert=True)
            return

        if user.balance_rub < (channel.price_per_post or 0):
            await callback.answer("❌ Недостаточно средств. Пополни баланс.", show_alert=True)
            return

        service = OrderService(session)
        try:
            order = await service.create_order(
                advertiser_id=user.id,
                channel_id=channel.id,
                channel_owner_id=channel.owner_id,
                channel_name=channel.title,
                post_text="",
                amount=channel.price_per_post,
            )
        except InsufficientBalanceError as e:
            await callback.answer(f"❌ {e}", show_alert=True)
            return

        await session.commit()

        await callback.message.answer(
            f"✅ <b>Заказ #{order.id} создан!</b>\n\n"
            f"Канал: {channel.title}\n"
            f"Сумма: {order.amount} ₽\n"
            f"Статус: ожидает подтверждения владельцем\n\n"
            f"Отправь текст поста, который хочешь разместить:",
            reply_markup=order_keyboard(order.id),
        )

    await callback.answer()


@router.message(F.text, F.chat.type == "private")
async def receive_post_text(message: Message, bot: Bot):
    """Принимает текст поста от рекламодателя после создания заказа."""
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(
                Order.advertiser_id == message.from_user.id,
                Order.status == "pending",
                Order.post_text == "",
            ).order_by(Order.created_at.desc()).limit(1)
        )
        order = result.scalar_one_or_none()
        if not order:
            return

        order.post_text = message.text[:4000]
        await session.commit()

        # Notify channel owner
        owner_result = await session.execute(select(User).where(User.id == order.channel_owner_id))
        owner = owner_result.scalar_one_or_none()

        if owner:
            await bot.send_message(
                chat_id=owner.id,
                text=(
                    f"📢 <b>Новый заказ на рекламу!</b>\n\n"
                    f"Канал: {order.channel_name}\n"
                    f"Сумма: {order.amount} ₽\n"
                    f"К получению: {order.owner_amount} ₽\n"
                    f"Текст поста:\n{order.post_text[:500]}\n\n"
                    f"У вас 24 часа на ответ."
                ),
                reply_markup=order_approve_keyboard(order.id),
            )

        await message.answer("✅ Текст поста сохранён. Ожидай подтверждения от владельца канала.")


@router.callback_query(F.data.startswith("order_skip:"))
async def cb_skip_post(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            await callback.answer("❌ Заказ не найден")
            return
        order.post_text = ""
        await session.commit()

        owner_result = await session.execute(select(User).where(User.id == order.channel_owner_id))
        owner = owner_result.scalar_one_or_none()
        if owner:
            await bot.send_message(
                chat_id=owner.id,
                text=(
                    f"📢 <b>Новый заказ на рекламу!</b>\n\n"
                    f"Канал: {order.channel_name}\n"
                    f"Сумма: {order.amount} ₽\n"
                    f"К получению: {order.owner_amount} ₽\n"
                    f"Текст поста не указан (можно добавить позже)\n\n"
                    f"У вас 24 часа на ответ."
                ),
                reply_markup=order_approve_keyboard(order.id),
            )
    await callback.message.edit_text("⏭ Текст поста пропущен. Ожидай подтверждения от владельца канала.")
    await callback.answer()


@router.callback_query(F.data.startswith("order_approve:"))
async def cb_approve_order(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        order_result = await session.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()
        if not order:
            await callback.answer("❌ Заказ не найден")
            return

        if order.channel_owner_id != callback.from_user.id:
            await callback.answer("❌ Это не ваш заказ", show_alert=True)
            return

        service = OrderService(session)
        try:
            await service.approve_order(order_id)
            await session.commit()
        except InvalidOrderStateError as e:
            await callback.answer(str(e), show_alert=True)
            return

    await callback.message.edit_text(
        f"✅ Заказ #{order_id} принят!\n"
        f"Средства зачислены на ваш баланс."
    )

    # Notify advertiser
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order:
            await bot.send_message(
                chat_id=order.advertiser_id,
                text=f"✅ Ваш заказ #{order_id} в канале {order.channel_name} принят! Пост будет опубликован.",
            )

    await callback.answer()


@router.callback_query(F.data.startswith("order_reject:"))
async def cb_reject_order(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        order_result = await session.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()
        if not order:
            await callback.answer("❌ Заказ не найден")
            return

        if order.channel_owner_id != callback.from_user.id:
            await callback.answer("❌ Это не ваш заказ", show_alert=True)
            return

        service = OrderService(session)
        try:
            await service.reject_order(order_id)
            await session.commit()
        except InvalidOrderStateError as e:
            await callback.answer(str(e), show_alert=True)
            return

    await callback.message.edit_text(
        f"❌ Заказ #{order_id} отклонён.\n"
        f"Средства возвращены рекламодателю."
    )

    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order:
            await bot.send_message(
                chat_id=order.advertiser_id,
                text=f"❌ Ваш заказ #{order_id} в канале {order.channel_name} отклонён владельцем. Средства возвращены.",
            )

    await callback.answer()
