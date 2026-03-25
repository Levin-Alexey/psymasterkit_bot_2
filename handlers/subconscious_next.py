from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent


router = Router()

RESULTS_TEXT = (
    "Например, наши пользователи благодаря работе с установками отмечают, что со временем:\n"
    "💰 <b>В деньгах</b>\n"
    " — начинают зарабатывать больше и перестают упираться в «финансовый потолок»\n"
    " — появляется больше возможностей и уверенности в своих решениях\n"
    " — деньги приходят легче, без постоянного напряжения\n"
    "❤️ <b>В отношениях</b>\n"
    " — уходят повторяющиеся сценарии и конфликты\n"
    " — становится легче выстраивать здоровые и тёплые отношения\n"
    " — появляется больше близости и понимания\n"
    "⚡ <b>В состоянии и энергии</b>\n"
    " — снижается тревожность и внутреннее напряжение\n"
    " — появляется больше энергии и спокойствия\n"
    " — уходит ощущение постоянной усталости\n"
    "🎯 <b>В реализации</b>\n"
    " — становится понятно, куда двигаться дальше\n"
    " — появляется смелость пробовать новое\n"
    " — цели начинают реализовываться легче\n"
    "А самое интересное - <b>меняется не только состояние, но и сами события в жизни.</b>\n"
    "Потому что когда меняются внутренние установки и реакции, меняются решения, которые человек принимает каждый день.\n"
    "А из этих решений постепенно складываются новые результаты и новая жизнь!\n"
    "И здесь возникает логичный вопрос: <b>Как научиться находить такие установки и менять их?</b> ⤵️"
)


def how_to_do_it_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Как это сделать?", callback_data="how_to_do_it")]
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


@router.callback_query(F.data == "what_next_subconscious")
async def open_what_next_screen(callback: CallbackQuery) -> None:
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
                event_code="what_next_subconscious_click",
                payload={"source": "subconscious_screen"},
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="results_examples_screen_open",
                payload={"step": "results_examples"},
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer_media_group(
            media=[
                InputMediaPhoto(media="https://iimg.su/i/Ljaw58"),
                InputMediaPhoto(media="https://iimg.su/i/g87IV1"),
            ]
        )
        await callback.message.answer(
            RESULTS_TEXT,
            reply_markup=how_to_do_it_keyboard(),
        )
