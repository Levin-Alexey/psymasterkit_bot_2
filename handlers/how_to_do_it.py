from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent


router = Router()

HOW_TEXT = (
    "<b>Теперь становится понятнее, почему иногда человек может:</b>\n"
    "- читать книги\n"
    "- проходить тренинги\n"
    "- обращаться к психологам\n"
    "- пытаться «взять себя в руки»\n"
    "но при этом состояние и жизнь <b>почти не меняются.</b>\n"
    "\n"
    "❌ Потому что чаще всего меняется только <b>поведение на уровне сознания</b>, "
    "а глубинные установки в подсознании остаются прежними.\n"
    "\n"
    "И тогда через время человек снова возвращается к привычным реакциям, решениям и результатам.\n"
    "\n"
    "Но возникает важный вопрос: <b>Можно ли изменить установки на уровне подсознания "
    "- и тем самым изменить свою жизнь?</b>\n"
    "\n"
    "- Да, можно!\n"
    "\n"
    "Для этого была создана методика <b>Master Kit</b> - система работы с подсознательными установками, "
    "которая помогает находить внутренние программы мышления и постепенно менять их.\n"
    "\n"
    "Хотите узнать, как это работает на практике? ⤵️"
)


def how_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Как?", callback_data="master_kit_how")]]
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


@router.callback_query(F.data == "how_to_do_it")
async def open_how_to_do_it_screen(callback: CallbackQuery) -> None:
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
                event_code="how_to_do_it_click",
                payload={"source": "results_examples_screen"},
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="master_kit_screen_open",
                payload={"step": "master_kit_intro"},
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer_media_group(
            media=[
                InputMediaPhoto(media="https://iimg.su/i/IfoQFT"),
                InputMediaPhoto(media="https://iimg.su/i/SIno6y"),
            ]
        )
        await callback.message.answer(
            HOW_TEXT,
            reply_markup=how_keyboard(),
        )