from aiogram import F, Router
from aiogram.types import CallbackQuery


router = Router()


async def show_next_screen(callback: CallbackQuery) -> None:
    """Display the next screen content after daily survey completion."""
    if callback.message is not None:
        await callback.message.answer(
            "Переход к следующему экрану готов. Пришлите текст и кнопки для следующего шага, и я добавлю их сюда."
        )


@router.callback_query(F.data == "go_next_screen")
async def open_next_screen(callback: CallbackQuery) -> None:
    await callback.answer()
    await show_next_screen(callback)