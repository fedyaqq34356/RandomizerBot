from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from storage import storage
from states import GiveawayManual
import keyboards as kb

router = Router()


@router.callback_query(F.data.startswith("add_participant_"))
async def add_participant_start(callback: CallbackQuery, state: FSMContext):
    giveaway_id = callback.data.replace("add_participant_", "")
    giveaway = storage.get_giveaway(giveaway_id)
    
    if not giveaway:
        await callback.answer("❌ Розіграш не знайдено", show_alert=True)
        return
    
    if callback.from_user.id != giveaway["admin_id"]:
        await callback.answer("❌ Ви не можете додавати учасників", show_alert=True)
        return
    
    await state.set_state(GiveawayManual.giveaway_id)
    await state.update_data(giveaway_id=giveaway_id)
    await state.set_state(GiveawayManual.username)
    
    await callback.message.edit_text(
        f"Додавання учасника до {giveaway_id}\n\n"
        "Введіть юзернейм учасника (без @):"
    )
    await callback.answer()


@router.message(GiveawayManual.username)
async def add_participant_username(msg: Message, state: FSMContext):
    if msg.text == "❌ Скасувати":
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    data = await state.get_data()
    giveaway_id = data["giveaway_id"]
    
    username = msg.text.replace("@", "")
    
    if storage.add_participant(giveaway_id, username):
        participants_count = len(storage.get_participants(giveaway_id))
        
        await msg.answer(
            f"✅ Учасника @{username} додано\n"
            f"Всього учасників: {participants_count}\n\n"
            "Введіть наступного учасника або натисніть 'Скасувати':",
            reply_markup=kb.cancel()
        )
    else:
        await msg.answer(
            f"⚠️ Учасник @{username} вже в списку\n\n"
            "Введіть іншого учасника:",
            reply_markup=kb.cancel()
        )


@router.callback_query(F.data == "participate")
async def participate_callback(callback: CallbackQuery):
    message = callback.message
    
    if not message.reply_markup or not message.reply_markup.inline_keyboard:
        await callback.answer("❌ Розіграш не знайдено", show_alert=True)
        return
    
    for row in message.reply_markup.inline_keyboard:
        for button in row:
            if "gw_" in button.callback_data:
                giveaway_id = button.callback_data
                break
    else:
        await callback.answer("❌ Помилка обробки", show_alert=True)
        return
    
    giveaway = storage.get_giveaway(giveaway_id)
    
    if not giveaway:
        await callback.answer("❌ Розіграш не знайдено", show_alert=True)
        return
    
    username = callback.from_user.username
    if not username:
        await callback.answer(
            "❌ У вас немає юзернейму. Встановіть юзернейм в налаштуваннях Telegram",
            show_alert=True
        )
        return
    
    if storage.add_participant(giveaway_id, username):
        participants_count = len(storage.get_participants(giveaway_id))
        await callback.answer(f"✅ Ви зареєстровані! Учасників: {participants_count}")
    else:
        await callback.answer("⚠️ Ви вже берете участь у цьому розіграші")
