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

DAY_OPTIONS: list[tuple[str, str]] = [
    ("d1", "Постоянно в делах и задачах"),
    ("d2", "Отвлекаюсь и откладываю дела"),
    ("d3", "Раздражение или напряжение"),
    ("d4", "День проходит на автомате"),
    ("d5", "В целом всё спокойно"),
]

DAY_OPTION_TEXT = {code: text for code, text in DAY_OPTIONS}

EVENING_OPTIONS: list[tuple[str, str]] = [
    ("e1", "Листаю телефон / соцсети"),
    ("e2", "Отдыхаю после тяжёлого дня"),
    ("e3", "Смотрю сериалы или видео"),
    ("e4", "Думаю о проблемах и будущем"),
    ("e5", "Провожу время спокойно"),
]

EVENING_OPTION_TEXT = {code: text for code, text in EVENING_OPTIONS}


def morning_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=f"morning_choice:{code}")]
            for code, text in MORNING_OPTIONS
        ]
    )


def day_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=f"day_choice:{code}")]
            for code, text in DAY_OPTIONS
        ]
    )


def evening_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=f"evening_choice:{code}")]
            for code, text in EVENING_OPTIONS
        ]
    )


async def save_step_answer(
    telegram_user_id: int,
    full_name: str | None,
    username: str | None,
    time_of_day: str,
    answer_text: str,
    event_code: str,
    choice_code: str,
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

        session.add(
            DailyAnswer(
                user_id=user.id,
                time_of_day=time_of_day,
                answer_text=answer_text,
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code=event_code,
                payload={"step": time_of_day, "choice_code": choice_code, "choice_text": answer_text},
            )
        )
        await session.commit()


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

    await save_step_answer(
        telegram_user_id=tg_user.id,
        full_name=tg_user.full_name,
        username=tg_user.username,
        time_of_day="morning",
        answer_text=answer_text,
        event_code="moning",
        choice_code=choice_code,
    )

    if callback.message is not None:
        await callback.message.answer(
            "А как обычно проходит ваш день? Что чаще всего вы чувствуете в течение дня? 👇🏼",
            reply_markup=day_keyboard(),
        )


@router.callback_query(F.data.startswith("day_choice:"))
async def handle_day_choice(callback: CallbackQuery) -> None:
    await callback.answer()

    tg_user = callback.from_user
    choice_code = (callback.data or "").split(":", maxsplit=1)[-1]
    answer_text = DAY_OPTION_TEXT.get(choice_code)

    if answer_text is None:
        if callback.message is not None:
            await callback.message.answer("Не удалось определить выбранный вариант. Попробуйте еще раз.")
        return

    await save_step_answer(
        telegram_user_id=tg_user.id,
        full_name=tg_user.full_name,
        username=tg_user.username,
        time_of_day="day",
        answer_text=answer_text,
        event_code="day",
        choice_code=choice_code,
    )

    if callback.message is not None:
        await callback.message.answer(
            "Теперь вспомните ваш обычный вечер. Как он чаще всего проходит?",
            reply_markup=evening_keyboard(),
        )


@router.callback_query(F.data.startswith("evening_choice:"))
async def handle_evening_choice(callback: CallbackQuery) -> None:
    await callback.answer()

    tg_user = callback.from_user
    choice_code = (callback.data or "").split(":", maxsplit=1)[-1]
    answer_text = EVENING_OPTION_TEXT.get(choice_code)

    if answer_text is None:
        if callback.message is not None:
            await callback.message.answer("Не удалось определить выбранный вариант. Попробуйте еще раз.")
        return

    await save_step_answer(
        telegram_user_id=tg_user.id,
        full_name=tg_user.full_name,
        username=tg_user.username,
        time_of_day="evening",
        answer_text=answer_text,
        event_code="evening",
        choice_code=choice_code,
    )

    if callback.message is not None:
        await callback.message.answer(
            "Ответ сохранён. Переходим к следующему экрану."
        )
        # Переход на следующий экран сразу после вечера
        from handlers.next_screen import show_next_screen
        await show_next_screen(callback)
