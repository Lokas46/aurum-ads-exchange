from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from app.database import async_session

from app.models.channel import Channel

from app.models.user import User

from app.config import settings

from bot.keyboards.channels import channel_keyboard, channels_list_keyboard, confirm_channel_keyboard

router = Router()


class AddChannel(StatesGroup):
    wait_chat_id = State()
    wait_description = State()
    wait_price = State()
    wait_categories = State()


@router.message(Command("add_channel"))
async def cmd_add_channel(message: Message, state: FSMContext):
    await message.answer(
        "📢 <b>Добавление канала</b>\n\n"
        "Перешли мне любое сообщение из твоего канала, чтобы я проверил права.\n\n"
        "<i>Убедись, что я добавлен в канал как администратор!</i>"
    )
    await state.set_state(AddChannel.wait_chat_id)


@router.message(AddChannel.wait_chat_id)
async def process_chat_id(message: Message, state: FSMContext):
    if not message.forward_from_chat:
        await message.answer("❌ Это не пересланное сообщение из канала. Попробуй ещё раз.")
        return

    chat = message.forward_from_chat
    await state.update_data(chat_id=chat.id, title=chat.title, username=chat.username)

    async with async_session() as session:
        existing = await session.execute(select(Channel).where(Channel.chat_id == chat.id))
        if existing.scalar_one_or_none():
            await message.answer("❌ Этот канал уже зарегистрирован в системе.")
            await state.clear()
            return

    await message.answer(
        f"✅ Канал <b>{chat.title}</b> найден.\n\n"
        f"Теперь напиши описание канала (что за тематика, чем интересен рекламодателям):"
    )
    await state.set_state(AddChannel.wait_description)


@router.message(AddChannel.wait_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "💰 Укажи цену за один рекламный пост (в ₽):"
    )
    await state.set_state(AddChannel.wait_price)


@router.message(AddChannel.wait_price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи корректную цену (число больше 0).")
        return
    await state.update_data(price=price)
    await message.answer(
        "🏷 Укажи категории через запятую (например: <i>крипта, трейдинг, новости</i>):"
    )
    await state.set_state(AddChannel.wait_categories)


@router.message(AddChannel.wait_categories)
async def process_categories(message: Message, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        channel = Channel(
            owner_id=message.from_user.id,
            title=data["title"],
            username=data.get("username"),
            chat_id=data["chat_id"],
            description=data["description"],
            price_per_post=data["price"],
            categories=message.text.lower().strip(),
        )
        session.add(channel)
        await session.commit()

        for admin_id in settings.admin_ids:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"🆕 <b>Новый канал на модерацию</b>\n\n"
                    f"Канал: {channel.title}\n"
                    f"Описание: {channel.description}\n"
                    f"Цена: {channel.price_per_post} ₽\n"
                    f"Категории: {channel.categories}\n\n"
                    f"Подтвердить: /approve_{channel.id}\n"
                    f"Отклонить: /reject_{channel.id}",
                )
            except Exception:
                pass

    await state.clear()
    await message.answer(
        "✅ <b>Канал отправлен на модерацию!</b>\n\n"
        "Администратор проверит его в ближайшее время."
    )


@router.message(F.text.startswith("/approve_"))
async def cmd_approve(message: Message):
    if message.from_user.id not in settings.admin_ids:
        return
    try:
        channel_id = int(message.text.split("_")[1])
    except (IndexError, ValueError):
        return

    async with async_session() as session:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()
        if channel:
            channel.is_moderated = True
            channel.is_active = True
            await session.commit()
            await message.answer(f"✅ Канал <b>{channel.title}</b> одобрен!")
            try:
                await message.bot.send_message(
                    channel.owner_id,
                    f"✅ Ваш канал <b>{channel.title}</b> прошёл модерацию и опубликован в каталоге!",
                )
            except Exception:
                pass


@router.message(F.text.startswith("/reject_"))
async def cmd_reject(message: Message):
    if message.from_user.id not in settings.admin_ids:
        return
    try:
        channel_id = int(message.text.split("_")[1])
    except (IndexError, ValueError):
        return

    async with async_session() as session:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()
        if channel:
            await session.delete(channel)
            await session.commit()
            await message.answer(f"❌ Канал <b>{channel.title}</b> отклонён.")
            try:
                await message.bot.send_message(
                    channel.owner_id,
                    f"❌ Ваш канал <b>{channel.title}</b> не прошёл модерацию.",
                )
            except Exception:
                pass


@router.callback_query(F.data.startswith("approve_"))
async def cb_approve_channel(callback: CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    try:
        channel_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Неверные данные")
        return

    async with async_session() as session:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()
        if channel:
            channel.is_moderated = True
            channel.is_active = True
            await session.commit()
            await callback.message.edit_text(f"✅ Канал <b>{channel.title}</b> одобрен!")
            try:
                await callback.bot.send_message(
                    channel.owner_id,
                    f"✅ Ваш канал <b>{channel.title}</b> прошёл модерацию и опубликован в каталоге!",
                )
            except Exception:
                pass
    await callback.answer()


@router.callback_query(F.data.startswith("reject_"))
async def cb_reject_channel(callback: CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    try:
        channel_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Неверные данные")
        return

    async with async_session() as session:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()
        if channel:
            await session.delete(channel)
            await session.commit()
            await callback.message.edit_text(f"❌ Канал <b>{channel.title}</b> отклонён.")
            try:
                await callback.bot.send_message(
                    channel.owner_id,
                    f"❌ Ваш канал <b>{channel.title}</b> не прошёл модерацию.",
                )
            except Exception:
                pass
    await callback.answer()


@router.callback_query(F.data.startswith("stats_"))
async def cb_channel_stats(callback: CallbackQuery):
    await callback.answer("📊 Статистика доступна в Mini App.", show_alert=True)


@router.callback_query(F.data.startswith("edit_"))
async def cb_channel_edit(callback: CallbackQuery):
    await callback.answer("✏️ Редактирование доступно в Mini App.", show_alert=True)


@router.callback_query(F.data.startswith("deactivate_"))
async def cb_channel_deactivate(callback: CallbackQuery):
    await callback.answer("🛑 Управление доступно в Mini App.", show_alert=True)
