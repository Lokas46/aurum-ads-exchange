from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select

from app.database import async_session

from app.models.user import User

from bot.keyboards.main import main_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == message.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name or "",
                last_name=message.from_user.last_name,
            )
            session.add(user)
            await session.commit()
        else:
            changed = False
            if message.from_user.username and message.from_user.username != user.username:
                user.username = message.from_user.username
                changed = True
            if message.from_user.first_name:
                user.first_name = message.from_user.first_name
                changed = True
            if changed:
                await session.commit()

    await message.answer(
        f"Добро пожаловать в <b>Ad Exchange</b>!\n\n"
        f"Здесь владельцы каналов продают рекламу, а рекламодатели покупают.\n\n"
        f"<b>Твой Telegram ID:</b> <code>{message.from_user.id}</code>\n\n"
        f"Выбери действие:",
        reply_markup=main_keyboard(message.from_user.id),
    )
