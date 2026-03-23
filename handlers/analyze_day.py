from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from db import SessionLocal
from models import DailyAnswer, User, UserEvent


router = Router()

MORNING_OPTIONS: list[tuple[str, str]] = [
    ("m1", "Тяжело просыпаюсь, нет энергии"),
    ("m2", "Сразу начинаю думать о делах"),
    ("m3", "Не хочется вставать"),
    ("m4", "Нормально, но без настроения"),
    ("m5", "Просыпаюсь бодрой"),
]

MORNING_OPTION_TEXT = {code: text for code, text in MORNING_OPTIONS}


def morning_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=f"morning_choice:{code}")]
            for code, text in MORNING_OPTIONS
        ]
    )


@router.callback_query(F.data == "analyze_day")
async def open_morning_step(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(
            "Представьте ваше обычное утро. Как чаще всего вы просыпаетесь?\n"
            "Выберите вариант, который ближе всего 👇🏼",
            reply_markup=morning_keyboard(),
        )


@router.callback_query(F.data.startswith("morning_choice:"))
async def handle_morning_choice(callback: CallbackQuery) -> None:
    await callback.answer()

    tg_user = callback.from_user
    choice_code = (callback.data or "").split(":", maxsplit=1)[-1]
    answer_text = MORNING_OPTION_TEXT.get(choice_code)

    if answer_text is None:
        if callback.message is not None:
            await callback.message.answer("Не удалось определить выбранный вариант. Попробуйте еще раз.")
        return

    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_user.id))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=tg_user.id,
                user_name=tg_user.full_name,
                telegram_username=tg_user.username,
            )
            session.add(user)
            await session.flush()

        session.add(
            DailyAnswer(
                user_id=user.id,
                time_of_day="morning",
                answer_text=answer_text,
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="moning",
                payload={"step": "morning", "choice_code": choice_code, "choice_text": answer_text},
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer(
            "Принято. Переходим к следующему шагу дневного разбора."
        )
