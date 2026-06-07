from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Отправить текст позже", callback_data=f"order_skip:{order_id}")],
    ])


def order_approve_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"order_approve:{order_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"order_reject:{order_id}"),
        ],
    ])
