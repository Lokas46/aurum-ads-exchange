from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from app.database import async_session

from app.models.channel import Channel

from app.config import settings

from bot.keyboards.main import main_keyboard

from bot.keyboards.channels import channels_list_keyboard

from bot.keyboards.wallet import wallet_keyboard

router = Router()


@router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выбери действие:",
        reply_markup=main_keyboard(callback.from_user.id),
    )
    await callback.answer()


@router.callback_query(F.data == "catalog")
async def cb_catalog(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Channel).where(Channel.is_active == True).where(Channel.is_moderated == True)
        )
        channels = result.scalars().all()

    if not channels:
        await callback.message.edit_text(
            "📭 <b>Каталог пуст</b>\n\nПока нет доступных каналов для рекламы.",
            reply_markup=main_keyboard(callback.from_user.id),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "📢 <b>Каталог каналов</b>\n\nВыбери канал для заказа рекламы:",
        reply_markup=channels_list_keyboard(channels),
    )
    await callback.answer()


@router.callback_query(F.data == "my_orders")
async def cb_my_orders(callback: CallbackQuery):
    await callback.message.edit_text(
        "📋 <b>Мои заказы</b>\n\n"
        "Функция будет доступна в Mini App.\n\n"
        "Нажми кнопку Mini App в главном меню.",
        reply_markup=main_keyboard(callback.from_user.id),
    )
    await callback.answer()


@router.callback_query(F.data == "add_channel")
async def cb_add_channel(callback: CallbackQuery):
    await callback.message.edit_text(
        "📢 <b>Регистрация канала</b>\n\n"
        "Используй команду /add_channel чтобы зарегистрировать канал.",
        reply_markup=main_keyboard(callback.from_user.id),
    )
    await callback.answer()


@router.callback_query(F.data == "open_miniapp")
async def cb_open_miniapp(callback: CallbackQuery):
    mini_app_url = f"{settings.api_base_url}/miniapp?user_id={callback.from_user.id}"
    await callback.message.answer(
        f"🔗 <b>Mini App</b>\n\n"
        f"Нажми кнопку «🔍 Mini App» в главном меню.",
        reply_markup=main_keyboard(callback.from_user.id),
    )
    await callback.answer()


@router.callback_query(F.data == "my_channels")
async def cb_my_channels(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Channel).where(Channel.owner_id == callback.from_user.id).order_by(Channel.created_at.desc())
        )
        channels = result.scalars().all()

    if not channels:
        await callback.message.edit_text(
            "📡 <b>Мои каналы</b>\n\nУ тебя пока нет зарегистрированных каналов.\n\nИспользуй /add_channel чтобы добавить канал.",
            reply_markup=main_keyboard(callback.from_user.id),
        )
        await callback.answer()
        return

    text = "📡 <b>Мои каналы</b>\n\n"
    for ch in channels:
        status = "✅ Активен" if ch.is_active else ("❌ Отклонён" if ch.is_moderated else "⏳ На модерации")
        text += f"• <b>{ch.title}</b> — {ch.price_per_post or '?'} ₽ — {status}\n"

    await callback.message.edit_text(text, reply_markup=main_keyboard(callback.from_user.id))
    await callback.answer()


@router.callback_query(F.data.in_({"admin_panel", "admin_check_payments"}))
async def cb_admin_moved(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Управление перенесено в Mini App.\n"
        "Нажми кнопку «🔍 Mini App» в главном меню.",
        reply_markup=main_keyboard(callback.from_user.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("channel_"))
async def cb_channel_detail(callback: CallbackQuery):
    channel_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()

    if not channel:
        await callback.answer("❌ Канал не найден")
        return

    text = (
        f"📢 <b>{channel.title}</b>\n\n"
        f"{channel.description or 'Нет описания'}\n\n"
        f"👥 Подписчиков: {channel.subscribers_count or 'не указано'}\n"
        f"💰 Цена: {channel.price_per_post or 'не указана'} ₽\n"
        f"🏷 Категории: {channel.categories or 'не указаны'}\n"
        f"{'✅ Верифицирован' if channel.is_verified else ''}"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Заказать рекламу", callback_data=f"create_order:{channel.id}"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="catalog"),
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
