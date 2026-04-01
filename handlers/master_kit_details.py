from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent


router = Router()

MASTER_KIT_DETAILS_TEXT = (
    "Автор методики - <b>Дарья Трутнева.</b>\n"
    "\n"
    "- Член Профессиональной Психотерапевтической Лиги и директор Научно-исследовательского института Саморегуляции,\n"
    "- Основатель международной компании Master Kit с оборотом более 1,5 млрд. руб\n"
    "- Исследователь психологии мышления и автор 5 книг по популярной психологии, одна из которых стала бестселлером на Ozon и переведена на 9 языков.\n"
    "\n"
    "Методика Дарьи Трутневой основана на принципах <b>когнитивной психологии, нейропсихологии и исследованиях работы мышления.</b>\n"
    "\n"
    "Но гораздо понятнее один раз увидеть, как именно работает этот механизм и за счёт чего происходят изменения.\n"
    "\n"
    "📹 <b>ПОСМОТРИТЕ КОРОТКОЕ ВИДЕО</b> - в нём наглядно показано, как работает методика и почему она помогает менять жизнь во всех сферах."
)


def master_kit_details_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Посмотреть видео",
                    url="https://youtu.be/NIRbJF-Olp0?is=AdmwYqjM-wR_nVNz",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Познакомиться с Дарьей",
                    url="https://t.me/dariatrutneva1/3835",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Как методика поможет мне",
                    callback_data="methodology_help_me",
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


@router.callback_query(F.data == "master_kit_details")
async def open_master_kit_details(callback: CallbackQuery) -> None:
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
                event_code="master_kit_details_click",
                payload={"source": "master_kit_info_screen"},
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="daria_trutneva_screen_open",
                payload={"step": "daria_trutneva_intro"},
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer_media_group(
            media=[
                InputMediaPhoto(media="https://iimg.su/i/WlMRfP"),
                InputMediaPhoto(media="https://iimg.su/i/8AI9xX"),
            ]
        )
        await callback.message.answer(
            MASTER_KIT_DETAILS_TEXT,
            reply_markup=master_kit_details_keyboard(),
        )
