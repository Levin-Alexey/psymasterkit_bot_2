from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent


router = Router()

HOW_IT_WORKS_FOR_ME_TEXT = (
    "Вы могли посмотреть на истории наших пользователей и подумать:\n"
    "«Им повезло.»\n"
    "«У них были другие обстоятельства.»\n"
    "«У меня всё сложнее.»\n"
    "Но если честно посмотреть на эти истории - у "
    "<b>большинства людей всё начиналось примерно одинаково.</b>\n"
    "С ощущения, что жизнь зашла в тупик.\n"
    "— кто-то жил в постоянной усталости\n"
    "— кто-то годами не мог выбраться из финансовых проблем\n"
    "— кто-то потерял себя в отношениях\n"
    "— кто-то просто чувствовал, что живёт не своей жизнью\n"
    "И в какой-то момент у каждого из них была <b>одна точка выбора</b> 👉🏼"
    "Ничего не менять или попробовать разобраться, "
    "<b>что на самом деле происходит внутри.</b>\n"
    "Потому что пока человек не видит свои внутренние установки, "
    "они продолжают незаметно управлять:\n"
    "- решениями\n"
    "- реакциями\n"
    "- состоянием\n"
    "- и в итоге всей жизнью.\n"
    "И именно поэтому один и тот же сценарий может повторяться годами.\n"
    "📌 <b>Но как только человек начинает видеть эти внутренние "
    "программы — появляется возможность изменить их.</b>\n"
    "И вместе с этим начинают меняться:\n"
    "— состояние\n"
    "— решения\n"
    "— действия\n"
    "— и постепенно вся реальность.\n"
    "Поэтому самый важный вопрос сейчас не в том, "
    "<b>получится ли изменить жизнь.</b>\n"
    "Вопрос в другом:\n"
    "Готовы ли вы <b>посмотреть на то, что происходит внутри "
    "вас на самом деле?</b>\n"
    "Если да - начните с первого шага ⤵️"
)


def try_master_kit_free_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Попробовать Master Kit бесплатно",
                    callback_data="try_methodology",
                )
            ]
        ]
    )


async def get_or_create_user(
    telegram_user_id: int,
    full_name: str | None,
    username: str | None,
) -> User:
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_user_id)
        )
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


@router.callback_query(F.data == "how_it_works_for_me")
async def open_how_it_works_for_me(callback: CallbackQuery) -> None:
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
                event_code="how_it_works_for_me_screen_open",
                payload={
                    "source": "more_stories_screen",
                    "next_step": "try_methodology",
                },
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer(
            HOW_IT_WORKS_FOR_ME_TEXT,
            reply_markup=try_master_kit_free_keyboard(),
        )
