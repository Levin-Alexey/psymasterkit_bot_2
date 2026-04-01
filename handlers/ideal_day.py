from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import desc, select

from db import SessionLocal
from models import DailyAnswer, User, UserEvent


router = Router()

IDEAL_DAY_TEXT = (
    "Закройте глаза на минуту и представьте ваш идеальный день.\n"
    "\n"
    "❤️ <b>День, в котором вам спокойно, интересно и приятно жить.</b>\n"
    "\n"
    "Попробуйте описать в нескольких словах:\n"
    "• каким было бы ваше утро\n"
    "• чем бы вы занимались днём\n"
    "• каким был бы ваш вечер\n"
    "\n"
    "Напишите это прямо здесь 👇🏼"
)


class IdealDayState(StatesGroup):
    waiting_for_answer = State()


def write_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Написать", callback_data="ideal_day_write")]]
    )


def reason_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Не хватает энергии", callback_data="reason_choice:r1")],
            [InlineKeyboardButton(text="Есть страх, что не получится", callback_data="reason_choice:r2")],
            [InlineKeyboardButton(text="Не понимаю, как изменить жизнь", callback_data="reason_choice:r3")],
            [InlineKeyboardButton(text="Мешают обстоятельства", callback_data="reason_choice:r4")],
            [InlineKeyboardButton(text="Что-то внутри мешает", callback_data="reason_choice:r5")],
            [InlineKeyboardButton(text="У меня все хорошо", callback_data="reason_choice:r6")],
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


async def add_user_event(
    telegram_user_id: int,
    full_name: str | None,
    username: str | None,
    event_code: str,
    payload: dict | None = None,
) -> None:
    user = await get_or_create_user(telegram_user_id, full_name, username)

    async with SessionLocal() as session:
        session.add(UserEvent(user_id=user.id, event_code=event_code, payload=payload))
        await session.commit()


async def get_last_answers_for_compare(user_id: int) -> tuple[str, str, str, str]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(DailyAnswer)
            .where(DailyAnswer.user_id == user_id)
            .where(DailyAnswer.time_of_day.in_(["morning", "day", "evening", "answer"]))
            .order_by(desc(DailyAnswer.created_at), desc(DailyAnswer.id))
        )
        rows = result.scalars().all()

    last_by_step: dict[str, str] = {}
    for row in rows:
        if row.time_of_day not in last_by_step:
            last_by_step[row.time_of_day] = row.answer_text

    morning = last_by_step.get("morning", "—")
    day = last_by_step.get("day", "—")
    evening = last_by_step.get("evening", "—")
    ideal = last_by_step.get("answer", "—")
    return morning, day, evening, ideal


@router.callback_query(F.data == "ideal_day")
async def open_ideal_day(callback: CallbackQuery) -> None:
    await callback.answer()

    await add_user_event(
        telegram_user_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        username=callback.from_user.username,
        event_code="ideal_day_screen_open",
        payload={"source": "ideal_day_button"},
    )

    if callback.message is not None:
        await callback.message.answer(IDEAL_DAY_TEXT, reply_markup=write_keyboard())


@router.callback_query(F.data == "ideal_day_write")
async def enable_ideal_day_input(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    await add_user_event(
        telegram_user_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        username=callback.from_user.username,
        event_code="ideal_day_write_click",
        payload={"source": "write_button"},
    )

    await state.set_state(IdealDayState.waiting_for_answer)
    if callback.message is not None:
        await callback.message.answer("Отлично. Напишите ваш идеальный день одним сообщением.")


@router.message(IdealDayState.waiting_for_answer)
async def save_ideal_day_answer(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Нужен текстовый ответ. Пожалуйста, опишите ваш идеальный день.")
        return

    user = await get_or_create_user(
        telegram_user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    async with SessionLocal() as session:
        session.add(
            DailyAnswer(
                user_id=user.id,
                time_of_day="answer",
                answer_text=text,
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="ideal_day_answer",
                payload={"step": "ideal_day", "answer_len": len(text)},
            )
        )
        await session.commit()

    compare_text = (
        "Теперь посмотрите на два сценария:\n"
        "\n"
        "1️⃣ <b>ваш реальный день</b>\n"
        "Утро: Нормально, но без настроения\n"
        "День: День проходит на автомате\n"
        "Вечер: Отдыхаю после тяжёлого дня\n"
        "\n"
        "2️⃣ <b>ваш идеальный день</b>🔥\n"
        "Между ними почти всегда есть разница.\n"
        "\n"
        "И теперь честно ответьте на один вопрос: <b>Почему вы пока не живёте так, как описали?</b>"
    )

    await add_user_event(
        telegram_user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
        event_code="reality_vs_ideal_screen_open",
        payload={"step": "compare_screen"},
    )

    await state.clear()
    await message.answer(compare_text, reply_markup=reason_keyboard())