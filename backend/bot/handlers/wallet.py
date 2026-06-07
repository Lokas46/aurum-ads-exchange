from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.user import User
from bot.keyboards.wallet import wallet_keyboard

router = Router()


@router.callback_query(F.data == "wallet")
async def cb_wallet(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == callback.from_user.id))
        user = result.scalar_one_or_none()

    rub_balance = user.balance_rub if user else 0

    await callback.message.edit_text(
        f"💰 <b>Кошелёк</b>\n\n"
        f"Баланс: <b>{rub_balance:.2f} ₽</b>\n\n"
        f"Пополнение: CryptoBot (USDT → ₽)\n"
        f"Вывод: CryptoBot (₽ → USDT)",
        reply_markup=wallet_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "wallet_deposit")
async def cb_deposit(callback: CallbackQuery):
    await callback.message.edit_text(
        "💳 <b>Пополнение баланса</b>\n\n"
        "Пополнение через CryptoBot:\n"
        "1. Нажми «Пополнить» в Mini App\n"
        "2. Оплати USDT через CryptoBot\n"
        "3. Средства сразу зачислятся на баланс\n\n"
        f"Курс: 1 USDT = {settings.cryptobot_usdt_rate:.0f} ₽\n"
        "Минимум: 10 USDT",
        reply_markup=wallet_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "wallet_withdraw")
async def cb_withdraw(callback: CallbackQuery):
    await callback.message.edit_text(
        "💸 <b>Вывод средств</b>\n\n"
        "Вывод через CryptoBot:\n"
        "1. Открой Mini App\n"
        "2. Введи сумму в ₽\n"
        "3. Укажи @username в CryptoBot\n\n"
        "Минимальная сумма: 500 ₽\n"
        "Комиссия: 0%",
        reply_markup=wallet_keyboard(),
    )
    await callback.answer()
