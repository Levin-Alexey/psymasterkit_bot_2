from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent


router = Router()

MASTER_KIT_TEXT = (
    "<b>Что такое Master Kit?</b>\n"
    "\n"
    "<b>Master kit</b> - научная методика и инструмент, который помогает трансформировать "
    "подсознательные установки и выходить из собственных ограничений, мешающих нам жить так, "
    "как мы хотели бы.\n"
    "\n"
    "<b>Она помогла 80 тысячам пользователям</b> пробить финансовый потолок, вывести отношения "
    "с близкими на новый уровень, перестать болеть и в целом улучшить качество жизни🔥\n"
    "\n"
    "Для изучения эффективности метода <b>в 2017 году был создан Научно-исследовательский "
    "институт саморегуляции</b>, где начали исследовать, как работа с установками влияет на "
    "состояние человека, поведение и качество ЖИЗНИ.\n"
    "\n"
    "Методика также получила <b>внимание международного научного сообщества</b>. Одним из "
    "экспертов, изучавших этот подход, стал <b>Майкл Нобель</b> - доктор психолого-\n"
    "педагогических наук и представитель семьи Нобелей.\n"
    "\n"
    "<b>Позже он стал официальным представителем методики Master Kit в мире науки.</b>"
)


def master_kit_info_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="ИСТОРИИ ПОЛЬЗОВАТЕЛЕЙ",
                    url="https://1000stories-mk.ru/?ysclid=mkvdq7ps2t580395367",
                )
            ],
            [InlineKeyboardButton(text="ИНСТИТУТ САМОРЕГУЛЯЦИИ", url="https://ya.ru")],
            [InlineKeyboardButton(text="Узнать подробнее", callback_data="master_kit_details")],
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


@router.callback_query(F.data == "master_kit_how")
async def open_master_kit_how_next(callback: CallbackQuery) -> None:
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
                event_code="master_kit_how_click",
                payload={"source": "master_kit_intro"},
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="master_kit_info_screen_open",
                payload={"step": "master_kit_info"},
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer_media_group(
            media=[
                InputMediaPhoto(media="https://iimg.su/i/MJmGQg"),
                InputMediaPhoto(media="https://iimg.su/i/T09RIm"),
            ]
        )
        await callback.message.answer(
            MASTER_KIT_TEXT,
            reply_markup=master_kit_info_keyboard(),
        )

