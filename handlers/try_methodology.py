from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from db import SessionLocal
from models import User, UserEvent


router = Router()

TRY_METHODOLOGY_TEXT = (
    "Чтобы вы могли попробовать методику на практике, в <b>Master Kit есть бесплатный вводный блок - 0 уровень</b>.\n"
    "Демо-доступ, который помогает:\n"
    " ✔ познакомиться с методикой\n"
    " ✔ попробовать первые проработки\n"
    " ✔ увидеть, как меняется состояние и реакции\n"
    " ✔ понять, как работают внутренние установки\n"
    "Это простой первый шаг, который позволяет почувствовать, как работает система и какие изменения она может запускать.\n"
    "Чтобы получить <b>бесплатный доступ</b>, оставьте ваши данные."
)


class TryMethodologyState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_email = State()


def phone_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 Напишите ваш телефон", callback_data="try_methodology_phone")]
        ]
    )


def email_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📧 Напишите ваш Email", callback_data="try_methodology_email")]
        ]
    )


def continue_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Продолжить", callback_data="try_methodology_continue")]]
    )


def final_links_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти на сайт", url="https://ya.ru")],
            [
                InlineKeyboardButton(
                    text="Перейти в Master Kit PRO",
                    url="https://t.me/freemoneymasterkit",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Перейти в Личный канал автора методики",
                    url="https://t.me/dariatrutneva1",
                )
            ],
        ]
    )


FINAL_TEXT = (
    "Мы получили ваши данные, в ближайшее время один из специалистов <b>Master Kit</b> свяжется с вами, чтобы:\n"
    " - помочь получить доступ к бесплатному блоку\n"
    " - показать, как пользоваться платформой\n"
    " - ответить на ваши вопросы\n"
    " - подсказать, с чего лучше начать работу\n"
    "И спасибо, что прошли этот путь вместе с нами 🙌\n\n"
    "В этом боте мы показали только небольшую часть того, как работает мышление и как внутренние установки могут влиять на жизнь.\n\n"
    "Если вам откликнулась эта тема и вы хотите продолжить разбираться глубже — вы всегда можете найти нас здесь:\n\n"
    "🌐 Официальный сайт Master Kit\n"
    "Здесь инструменты и навыки работы с мышлением, которые помогут достичь целей и повысить норму жизни.\n\n"
    "🎓 Master Kit PRO\n"
    "Сообщество и пространство для более глубокой работы с мышлением, практиками и развитием.\n\n"
    "🔥Личный канал автора методики - Дарьи Трутневой\n\n"
    "Мы регулярно публикуем:\n\n"
    "— новые материалы о работе мышления\n"
    "— разборы жизненных ситуаций\n"
    "— практические инструменты\n"
    "— истории изменений пользователей\n\n"
    "Иногда даже один шаг в сторону осознанности может изменить направление всей жизни.\n\n"
    "До встречи 🤍"
)


async def send_to_n8n_stub(user: User) -> dict:
    # Заглушка: здесь будет реальный POST-запрос в n8n webhook для отправки лида в amoCRM.
    return {
        "status": "stub",
        "amo_crm_sent": False,
        "telegram_id": user.telegram_id,
        "phone_exists": bool(user.phone),
        "email_exists": bool(user.email),
    }


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


@router.callback_query(F.data == "try_methodology")
async def open_try_methodology_screen(callback: CallbackQuery) -> None:
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
                event_code="try_methodology_click",
                payload=None,
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="try_methodology_screen_open",
                payload={"source": "ideal_day_return_screen"},
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer(
            TRY_METHODOLOGY_TEXT,
            reply_markup=phone_keyboard(),
        )


@router.callback_query(F.data == "try_methodology_phone")
async def enable_phone_input(callback: CallbackQuery, state: FSMContext) -> None:
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
                event_code="phone_input_click",
                payload={"source": "try_methodology_screen"},
            )
        )
        await session.commit()

    await state.set_state(TryMethodologyState.waiting_for_phone)
    if callback.message is not None:
        await callback.message.answer("Отправьте ваш номер телефона одним сообщением.")


@router.message(TryMethodologyState.waiting_for_phone)
async def save_phone(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if not phone:
        await message.answer("Пожалуйста, отправьте номер телефона текстом.")
        return

    user = await get_or_create_user(
        telegram_user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    async with SessionLocal() as session:
        db_user = await session.get(User, user.id)
        if db_user is None:
            await message.answer("Не удалось сохранить номер. Попробуйте еще раз.")
            return

        db_user.phone = phone
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="phone_saved",
                payload={"phone_len": len(phone)},
            )
        )
        await session.commit()

    await state.clear()
    await message.answer(
        "Телефон сохранен. Теперь укажите email.",
        reply_markup=email_keyboard(),
    )


@router.callback_query(F.data == "try_methodology_email")
async def enable_email_input(callback: CallbackQuery, state: FSMContext) -> None:
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
                event_code="email_input_click",
                payload={"source": "phone_saved_screen"},
            )
        )
        await session.commit()

    await state.set_state(TryMethodologyState.waiting_for_email)
    if callback.message is not None:
        await callback.message.answer("Отправьте ваш email одним сообщением.")


@router.message(TryMethodologyState.waiting_for_email)
async def save_email(message: Message, state: FSMContext) -> None:
    email = (message.text or "").strip()
    if not email:
        await message.answer("Пожалуйста, отправьте email текстом.")
        return

    user = await get_or_create_user(
        telegram_user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    async with SessionLocal() as session:
        db_user = await session.get(User, user.id)
        if db_user is None:
            await message.answer("Не удалось сохранить email. Попробуйте еще раз.")
            return

        db_user.email = email
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="email_saved",
                payload={"email_len": len(email)},
            )
        )
        await session.commit()

    await state.clear()
    await message.answer(
        "Спасибо, данные сохранены.",
        reply_markup=continue_keyboard(),
    )


@router.callback_query(F.data == "try_methodology_continue")
async def open_final_screen(callback: CallbackQuery) -> None:
    await callback.answer()

    user = await get_or_create_user(
        telegram_user_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        username=callback.from_user.username,
    )

    n8n_result = await send_to_n8n_stub(user)

    async with SessionLocal() as session:
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="try_methodology_continue_click",
                payload={"source": "email_saved"},
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="final_contacts_screen_open",
                payload={"source": "try_methodology_continue"},
            )
        )
        session.add(
            UserEvent(
                user_id=user.id,
                event_code="n8n_send_stub",
                payload=n8n_result,
            )
        )
        await session.commit()

    if callback.message is not None:
        await callback.message.answer(
            FINAL_TEXT,
            reply_markup=final_links_keyboard(),
        )
