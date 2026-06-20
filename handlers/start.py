from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_IDS
import keyboards as kb

router = Router()


@router.message(Command("start"))
async def start(msg: Message):
    if msg.from_user.id in ADMIN_IDS:
        await msg.answer(
            "🎁 Вітаю! Оберіть дію:",
            reply_markup=kb.admin_main()
        )
    else:
        await msg.answer(
            "🎁 Вітаю! Тут ви можете переглянути доступні розіграші.",
            reply_markup=kb.user_main()
        )
