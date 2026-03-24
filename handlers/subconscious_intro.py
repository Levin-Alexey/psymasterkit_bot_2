from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent


router = Router()


async def get_or_create_user(
    telegram_user_id: int,
    full_name: str | None,
    username: str | None,
) -> User:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_user_id))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=telegram_user_id,
                user_name=full_name,
                telegram_username=username,
            )
            session.add(user)
            await session.flush()
        else:
            user.user_name = full_name
            user.telegram_username = username

        await session.commit()
        await session.refresh(user)
        return user


@router.callback_query(F.data == "subconscious_learn")
async def open_subconscious_next_screen(callback: CallbackQuery) -> None:
    await callback.answer()

    user = await get_or_create_user(
        telegram_user_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        username=callback.from_user.username,
    )

    async with SessionLocal() as session:
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="subconscious_learn_click",
                payload={"source": "subconscious_intro"},
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer(
            "Переходим к следующему экрану про подсознание. Пришлите следующий текст и кнопки, и я добавлю их сюда."
        )