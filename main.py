import asyncio
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv
from sqlalchemy import select

from db import SessionLocal, init_models
from handlers import (
	analyze_day_router,
	how_to_do_it_router,
	ideal_day_router,
	master_kit_details_router,
	master_kit_how_router,
	methodology_help_router,
	next_screen_router,
	reason_choice_router,
	subconscious_intro_router,
	subconscious_next_router,
	try_methodology_router,
)
from models import User, UserEvent


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

router = Router()

START_TEXT = (
	"Добро пожаловать!\n"
	"Этот бот поможет вам <b>по-другому посмотреть на свою жизнь через ваш обычный день.</b>\n\n"
	"Мы создали его вместе с психологами и специалистами по работе с мышлением, "
	"которые ежедневно работают с людьми и их внутренними состояниями.\n\n"
	"<b>В процессе вы:</b>\n\n"
	"- разберёте свой обычный день\n"
	"- сформулируете свой <b>идеальный день</b>\n"
	"- увидите, какие внутренние программы мешают изменениям\n"
	"- узнаете, какие инструменты помогают менять состояние и жизнь\n"
	"Это небольшой, но очень показательный разбор.\n"
	"Начнём с первого шага 👇🏼\n"
	"Давайте посмотрим, <b>как проходит ваш обычный день.</b>"
)


def start_keyboard() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(
		inline_keyboard=[
			[InlineKeyboardButton(text="Разобрать мой день", callback_data="analyze_day")]
		]
	)


async def upsert_user(message: Message) -> User | None:
	tg_user = message.from_user
	if tg_user is None:
		return None

	async with SessionLocal() as session:
		query = select(User).where(User.telegram_id == tg_user.id)
		result = await session.execute(query)
		user = result.scalar_one_or_none()

		if user is None:
			user = User(
				telegram_id=tg_user.id,
				user_name=tg_user.full_name,
				telegram_username=tg_user.username,
			)
			session.add(user)
			await session.flush()
		else:
			user.user_name = tg_user.full_name
			user.telegram_username = tg_user.username

		await session.commit()
		return user


async def add_user_event(user_id: int, event_code: str, payload: dict | None = None) -> None:
	async with SessionLocal() as session:
		session.add(UserEvent(user_id=user_id, event_code=event_code, payload=payload))
		await session.commit()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
	user = await upsert_user(message)

	if user is not None:
		await add_user_event(
			user_id=user.id,
			event_code="start",
			payload={"chat_id": message.chat.id, "trigger": "command_start"},
		)

	await message.answer(START_TEXT, reply_markup=start_keyboard())


async def main() -> None:
	if not BOT_TOKEN:
		raise RuntimeError("BOT_TOKEN is empty in .env")

	await init_models()

	bot = Bot(
		token=BOT_TOKEN,
		default=DefaultBotProperties(parse_mode=ParseMode.HTML),
	)
	dp = Dispatcher()
	dp.include_router(router)
	dp.include_router(analyze_day_router)
	dp.include_router(next_screen_router)
	dp.include_router(ideal_day_router)
	dp.include_router(reason_choice_router)
	dp.include_router(subconscious_intro_router)
	dp.include_router(subconscious_next_router)
	dp.include_router(how_to_do_it_router)
	dp.include_router(master_kit_how_router)
	dp.include_router(master_kit_details_router)
	dp.include_router(methodology_help_router)
	dp.include_router(try_methodology_router)

	await dp.start_polling(bot)


if __name__ == "__main__":
	asyncio.run(main())
