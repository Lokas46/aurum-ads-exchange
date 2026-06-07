from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def wallet_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Пополнить", callback_data="wallet_deposit"),
        InlineKeyboardButton(text="💸 Вывести", callback_data="wallet_withdraw"),
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"),
    )
    return builder.as_markup()
