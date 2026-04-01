from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent


router = Router()

SUBCONSCIOUS_TEXT = (
    "Мы часто думаем, что наша жизнь зависит только от наших решений и усилий.\n"
    "\n"
    "<b>Но на самом деле наш мозг работает на двух уровнях: сознания и подсознания.</b>\n"
    "\n"
    "И именно подсознание во многом определяет:\n"
    " - как мы реагируем на события\n"
    " - какие решения принимаем\n"
    " - какое состояние испытываем\n"
    " - и какие результаты снова и снова получаем в жизни\n"
    "\n"
    "Поэтому иногда возникает странное ощущение: головой мы хотим одного, "
    "<b>а в реальности получается совсем другое.</b>\n"
    "\n"
    "Почему так происходит?\n"
    "\n"
    "👉🏼 Потому что в подсознании постепенно формируются <b>внутренние установки</b> "
    "- незаметные программы мышления, которые появляются из:\n"
    "- прошлого опыта\n"
    "- воспитания\n"
    "- фраз, которые мы слышали в детстве\n"
    "- сильных эмоций и переживаний\n"
    "\n"
    "Со временем они начинают автоматически влиять на наше состояние и реакции. "
    "И человек может даже не замечать этого. Но <b>именно из этих реакций постепенно складываются:</b>\n"
    "- уровень энергии\n"
    "- привычные решения\n"
    "- эмоциональное состояние\n"
    "- и то, каким становится наш обычный день.\n"
    "\n"
    "📍А из дней постепенно формируется вся жизнь. Поэтому часто дело не только в усилиях. "
    "Сначала важно понять, какие установки уже работают внутри нас.\n"
    "\n"
    "Мы подготовили короткое <b>видео, которое наглядно показывает, как взаимодействуют "
    "сознание и подсознание</b> - и почему это так влияет на нашу жизнь.\n"
    "\n"
    "Посмотрите его ⤵️"
)


def subconscious_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Посмотреть видео", url="https://ya.ru")],
            [InlineKeyboardButton(text="Что делать дальше?", callback_data="what_next_subconscious")],
        ]
    )


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
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="subconscious_screen_open",
                payload={"step": "subconscious_explanation"},
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer(
            SUBCONSCIOUS_TEXT,
            reply_markup=subconscious_keyboard(),
        )