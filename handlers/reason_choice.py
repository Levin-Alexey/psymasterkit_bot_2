from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent


router = Router()

REASON_SCREEN_TEXT = (
    "Интересно, что большинство людей выбирают эти варианты:\n\n"
    "- нет энергии\n"
    "- обстоятельства\n"
    "- непонятно как изменить жизнь\n\n"
    "И на первый взгляд это действительно кажется причиной. Но в реальности чаще всего дело не в этом.\n\n"
    "Потому что можно поменять работу, город, окружение... но через время жизнь снова начинает выглядеть похожим образом.\n\n"
    "Почему так происходит? \n\n"
    "Потому что в нашем подсознании постепенно формируются внутренние установки, которые незаметно начинают управлять решениями и состоянием.\n"
    "Например:\n"
    "- «мне уже поздно что-то менять»\n"
    "- «надо просто терпеть»\n"
    "- «у меня всё равно не получится»\n"
    "- «так живут все»\n"
    "Мы редко их замечаем, но именно они часто задают направление жизни.\n"
    "Давайте разберёмся, <b>как работает подсознание и что это за установки, как они влияют на нас</b> ⤵️"
)

REASON_TEXT_BY_CODE = {
    "r1": "Не хватает энергии",
    "r2": "Есть страх, что не получится",
    "r3": "Не понимаю, как изменить жизнь",
    "r4": "Мешают обстоятельства",
    "r5": "Что-то внутри мешает",
    "r6": "У меня все хорошо",
}


def learn_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Узнать", callback_data="subconscious_learn")]]
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


@router.callback_query(F.data.startswith("reason_choice:"))
async def handle_reason_choice(callback: CallbackQuery) -> None:
    await callback.answer()

    choice_code = (callback.data or "").split(":", maxsplit=1)[-1]
    choice_text = REASON_TEXT_BY_CODE.get(choice_code, "unknown")

    user = await get_or_create_user(
        telegram_user_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        username=callback.from_user.username,
    )

    async with SessionLocal() as session:
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="reason_choice",
                payload={"step": "reason_choice", "choice_code": choice_code, "choice_text": choice_text},
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="subconscious_intro_open",
                payload={"source_step": "reason_choice", "choice_code": choice_code},
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer(
            REASON_SCREEN_TEXT,
            reply_markup=learn_keyboard(),
        )