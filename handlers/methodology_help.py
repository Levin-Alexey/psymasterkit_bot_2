from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent

METHODOLOGY_HELP_TEXT = (
    "<b>А теперь вернемся к вашему идеальному дню</b> 🔥\n"
    "— К тому дню, где вы просыпаетесь с большим количеством энергии.\n"
    "— Где внутри больше спокойствия и уверенности\n"
    "— Где в течение дня есть ощущение, что вы живёте свою жизнь, а не просто проживаете очередной день на автомате!\n\n"
    "Между тем днём, который есть сейчас, и тем днём, который вы описали, обычно лежит <b>не одно большое решение</b>, а множество маленьких изменений.\n\n"
    "Меняется то, как проходит утро.\n"
    "Меняется состояние в течение дня.\n"
    "Меняются решения, которые человек принимает.\n\n"
    "И именно из этих изменений постепенно складывается новая жизнь.\n\n"
    "❤️Методика <b>Master Kit</b> как раз помогает запустить этот процесс.  Шаг за шагом она позволяет менять внутренние реакции и привычные сценарии, из которых формируется наш обычный день.\n\n"
    "И тогда тот день, который вы описали как идеальный, постепенно начинает становиться реальностью.\n"
    "👇"
)


def try_methodology_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Попробовать методику", callback_data="try_methodology")]
        ]
    )


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


@router.callback_query(F.data == "methodology_help_me")
async def open_methodology_help_screen(callback: CallbackQuery) -> None:
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
                event_code="methodology_help_me_click",
                payload={"source": "daria_trutneva_screen"},
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="ideal_day_return_screen_open",
                payload=None,
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer(
            METHODOLOGY_HELP_TEXT,
            reply_markup=try_methodology_keyboard(),
        )