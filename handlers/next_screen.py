from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent


router = Router()

NEXT_SCREEN_TEXT = (
    "Интересно, что большинство людей описывают примерно один и тот же цикл:\n"
    "<b>утро без энергии → день на автомате → вечер без сил.</b>\n"
    "Со временем в таком режиме появляется ощущение, что:\n"
    "— дни становятся похожими друг на друга\n"
    "— энергия постепенно уменьшается\n"
    "— а настоящие изменения всё время откладываются\n"
    "💔И в какой-то момент возникает чувство, что жизнь будто <b>проходит где-то рядом.</b>\n"
    "Самое сложное в этом состоянии — оно кажется обычным.\n"
    "Человек привыкает. Но именно из таких дней постепенно формируются:\n"
    "— хроническая усталость\n"
    "— потеря интереса\n"
    "— тревога о будущем\n"
    "— ощущение, что вы живёте не той жизнью\n"
    "⭐️И хорошая новость в том, что всё можно увидеть намного яснее и наконец изменить!\n"
    "Давайте сделаем следующий шаг — Попробуем представить ваш идеальный день 👇🏼"
)


def ideal_day_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мой идеальный день", callback_data="ideal_day")]
        ]
    )


async def add_user_event(
    telegram_user_id: int,
    full_name: str | None,
    username: str | None,
    event_code: str,
    payload: dict | None = None,
) -> None:
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

        session.add(UserEvent(user_id=user.id, event_code=event_code, payload=payload))
        await session.commit()


async def show_next_screen(callback: CallbackQuery) -> None:
    await add_user_event(
        telegram_user_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        username=callback.from_user.username,
        event_code="cycle_screen_open",
        payload={"source": callback.data or "unknown"},
    )

    if callback.message is not None:
        await callback.message.answer(
            NEXT_SCREEN_TEXT,
            reply_markup=ideal_day_keyboard(),
        )


@router.callback_query(F.data == "go_next_screen")
async def open_next_screen(callback: CallbackQuery) -> None:
    await callback.answer()
    await show_next_screen(callback)