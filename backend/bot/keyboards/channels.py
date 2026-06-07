from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def channel_keyboard(channel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data=f"stats_{channel_id}"),
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{channel_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🛑 Снять с публикации", callback_data=f"deactivate_{channel_id}"),
    )
    return builder.as_markup()


def channels_list_keyboard(channels: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        price = f"{ch.price_per_post} ₽" if ch.price_per_post else "цена не указана"
        label = f"{ch.title} — {price}"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"channel_{ch.id}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()


def confirm_channel_keyboard(channel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_{channel_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{channel_id}"),
    )
    return builder.as_markup()
