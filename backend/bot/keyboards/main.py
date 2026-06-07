from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings


def main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📢 Каталог каналов", callback_data="catalog"),
        InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_channel"),
    )
    builder.row(
        InlineKeyboardButton(text="📡 Мои каналы", callback_data="my_channels"),
        InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders"),
    )
    builder.row(
        InlineKeyboardButton(text="💰 Кошелёк", callback_data="wallet"),
        InlineKeyboardButton(text="🔍 Mini App", web_app=WebAppInfo(url=f"{settings.api_base_url}/miniapp")),
    )
    return builder.as_markup()
