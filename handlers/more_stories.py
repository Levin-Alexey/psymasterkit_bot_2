from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent


router = Router()

MORE_STORIES_TEXT = (
    "Мы показали лишь часть историй.\n"
    "Но у методики Master Kit тысячи реальных результатов — и за каждой историей стоит момент, когда человек чувствовал, что <b>жизнь зашла в тупик.</b>\n"
    "Посмотрите ещё несколько историй пользователей. Возможно, одна из них окажется особенно близкой вам 👇\n"
    "1️⃣ <b>Семейный кризис после рождения ребёнка</b> (Асель и Нияз)\n"
    "История супружеской пары, которая столкнулась с сильным кризисом после рождения ребёнка. Боль, претензии, агрессия и почти разрушенные отношения — и путь к восстановлению семьи через работу над собой.\n"
    "2️⃣ <b>Потеря близкого, депрессия и диагноз «бесплодие»</b> (Алина)\n"
    "Смерть брата, тяжёлая депрессия, кризис в семье и бизнесе, диагноз бесплодия. Когда казалось, что выхода из этой чёрной полосы нет — Алина начала менять мышление и постепенно изменила свою жизнь.\n"
    "3️⃣ <b>Страх повторить семейный сценарий зависимости</b> (Аэлита)\n"
    "История о внутренней пустоте, страхе потерять себя и повторить разрушительные семейные сценарии. Через работу с установками Аэлита смогла прийти к внутреннему исцелению, новым отношениям и самореализации.\n"
    "4️⃣ <b>Ощущение, что живёшь не своей жизнью</b> (Иван)\n"
    "Несмотря на стабильную работу, Иван чувствовал тревогу и ощущение, что жизнь проходит мимо. Через работу с мышлением он смог изменить цели, найти новый формат работы, улучшить качество жизни и реализовать свои мечты."
)


def more_stories_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1️⃣ Семейный кризис",
                    url="https://youtu.be/ILQM33cTxzs?utm_source=saitstatia",
                )
            ],
            [
                InlineKeyboardButton(
                    text="2️⃣ Депрессия и диагноз «бесплодие»",
                    url="https://www.youtube.com/watch?v=mEYZr3KKT_M&utm_source=saitstatia",
                )
            ],
            [
                InlineKeyboardButton(
                    text="3️⃣ Страх семейного сценария зависимости",
                    url="https://www.youtube.com/watch?v=kaR0X3fXg1s&t=10s&utm_source=saitstatia",
                )
            ],
            [
                InlineKeyboardButton(
                    text="4️⃣ Ощущение, что живёшь не своей жизнью",
                    url="https://youtu.be/MaM-vJykwGs?utm_source=saitstatia",
                )
            ],
            [
                InlineKeyboardButton(
                    text="5️⃣ как это работает для меня",
                    callback_data="how_it_works_for_me",
                )
            ],
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


@router.callback_query(F.data == "more_stories")
async def open_more_stories(callback: CallbackQuery) -> None:
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
                event_code="more_stories_screen_open",
                payload={"source": "n8n", "trigger": "more_stories"},
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer(
            MORE_STORIES_TEXT,
            reply_markup=more_stories_keyboard(),
        )
