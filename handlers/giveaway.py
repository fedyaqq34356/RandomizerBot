from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS, MAX_WINNERS
from storage import storage
from states import GiveawayCreate
import keyboards as kb

router = Router()


@router.message(F.text == "🎁 Створити розіграш")
async def create_giveaway_start(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    await state.set_state(GiveawayCreate.mode)
    await msg.answer(
        "Виберіть режим розіграшу:",
        reply_markup=kb.giveaway_mode()
    )


@router.callback_query(F.data.in_(["mode_bot", "mode_user"]))
async def select_mode(callback: CallbackQuery, state: FSMContext):
    mode = "bot" if callback.data == "mode_bot" else "user"
    
    if mode == "user":
        accounts = storage.get_user_accounts(callback.from_user.id)
        if not accounts:
            await callback.answer("❌ Спочатку додайте user-акаунт", show_alert=True)
            await state.clear()
            return
    
    await state.update_data(mode=mode)
    await state.set_state(GiveawayCreate.text)
    
    await callback.message.edit_text(
        f"Режим: {'🤖 Бот' if mode == 'bot' else '👤 User-акаунт'}\n\n"
        "✉️ Введіть текст розіграшу:"
    )
    await callback.answer()


@router.message(GiveawayCreate.text)
async def enter_text(msg: Message, state: FSMContext):
    if msg.text == "❌ Скасувати":
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    await state.update_data(text=msg.text)
    await state.set_state(GiveawayCreate.button_text)
    
    await msg.answer(
        "✉️ Введіть текст кнопки участі:",
        reply_markup=kb.cancel()
    )


@router.message(GiveawayCreate.button_text)
async def enter_button_text(msg: Message, state: FSMContext):
    if msg.text == "❌ Скасувати":
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    await state.update_data(button_text=msg.text, channels=[])
    await state.set_state(GiveawayCreate.channels)
    
    await msg.answer(
        "➕ Надішліть юзернейм каналу (@channel) або перешліть повідомлення з каналу.\n\n"
        "Можна додати кілька каналів по черзі.\n"
        "Натисніть 'Пропустити' для розіграшу без обов'язкових підписок.",
        reply_markup=kb.skip_channels()
    )


@router.callback_query(F.data == "skip_channels")
async def skip_channels(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GiveawayCreate.winners_count)
    await callback.message.edit_text("🏆 Введіть кількість переможців:")
    await callback.answer()


@router.callback_query(F.data == "finish_channels")
async def finish_channels(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GiveawayCreate.winners_count)
    await callback.message.edit_text("🏆 Введіть кількість переможців:")
    await callback.answer()


@router.message(GiveawayCreate.channels)
async def add_channel(msg: Message, state: FSMContext):
    if msg.text == "❌ Скасувати":
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    data = await state.get_data()
    channels = data.get("channels", [])
    
    channel = None
    if msg.text and msg.text.startswith("@"):
        channel = msg.text
    elif msg.forward_from_chat:
        channel = f"@{msg.forward_from_chat.username}" if msg.forward_from_chat.username else str(msg.forward_from_chat.id)
    
    if channel:
        if channel not in channels:
            channels.append(channel)
            await state.update_data(channels=channels)
            await msg.answer(
                f"✅ Канал {channel} додано\n"
                f"Всього каналів: {len(channels)}\n\n"
                "Додайте ще канал або натисніть 'Завершити'",
                reply_markup=kb.finish_channels()
            )
        else:
            await msg.answer("⚠️ Цей канал вже додано")
    else:
        await msg.answer("❌ Невірний формат. Надішліть @username або перешліть повідомлення")


@router.message(GiveawayCreate.winners_count)
async def enter_winners_count(msg: Message, state: FSMContext):
    if msg.text == "❌ Скасувати":
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    try:
        count = int(msg.text)
        if count < 1:
            await msg.answer("❌ Кількість переможців має бути більше 0")
            return
        
        if count > MAX_WINNERS:
            await msg.answer(
                f"❌ Максимальна кількість переможців: {MAX_WINNERS}\n"
                "Введіть число менше:"
            )
            return
        
        data = await state.get_data()
        
        giveaway_id = storage.create_giveaway(
            msg.from_user.id,
            data["mode"],
            data["text"],
            data["button_text"],
            data.get("channels", []),
            count
        )
        
        await state.clear()
        
        mode_text = "🤖 Бот" if data["mode"] == "bot" else "👤 User-акаунт"
        channels_text = "\n".join(data.get("channels", [])) if data.get("channels") else "Немає"
        
        await msg.answer(
            f"✅ Розіграш створено!\n\n"
            f"ID: {giveaway_id}\n"
            f"Режим: {mode_text}\n"
            f"Текст: {data['text']}\n"
            f"Кнопка: {data['button_text']}\n"
            f"Канали: {channels_text}\n"
            f"Переможців: {count}",
            reply_markup=kb.admin_main()
        )
        
    except ValueError:
        await msg.answer("❌ Введіть число")


@router.message(F.text == "📋 Мої розіграші")
async def my_giveaways(msg: Message):
    user_id = msg.from_user.id
    
    if user_id in ADMIN_IDS:
        giveaways = storage.get_admin_giveaways(user_id)
    else:
        giveaways = {}
    
    if not giveaways:
        await msg.answer("У вас немає розіграшів")
        return
    
    text = "📋 Ваші розіграші:\n\n"
    for gid, data in giveaways.items():
        participants_count = len(storage.get_participants(gid))
        winners_count = len(storage.get_winners(gid))
        
        mode_emoji = "🤖" if data["mode"] == "bot" else "👤"
        status_emoji = "🟢" if data["status"] == "active" else "🔴"
        
        text += (
            f"{status_emoji} {mode_emoji} {gid}\n"
            f"Текст: {data['text'][:30]}...\n"
            f"Учасників: {participants_count}\n"
            f"Переможців: {winners_count}/{data['winners_count']}\n\n"
        )
    
    await msg.answer(text)


@router.message(F.text.startswith("gw_"))
async def giveaway_details(msg: Message):
    giveaway_id = msg.text
    giveaway = storage.get_giveaway(giveaway_id)
    
    if not giveaway:
        await msg.answer("❌ Розіграш не знайдено")
        return
    
    if msg.from_user.id not in ADMIN_IDS and msg.from_user.id != giveaway["admin_id"]:
        return
    
    participants = storage.get_participants(giveaway_id)
    winners = storage.get_winners(giveaway_id)
    
    mode_text = "🤖 Бот" if giveaway["mode"] == "bot" else "👤 User-акаунт"
    channels_text = "\n".join(giveaway["channels"]) if giveaway["channels"] else "Немає"
    
    text = (
        f"📊 Інформація про розіграш\n\n"
        f"ID: {giveaway_id}\n"
        f"Режим: {mode_text}\n"
        f"Текст: {giveaway['text']}\n"
        f"Кнопка: {giveaway['button_text']}\n"
        f"Канали: {channels_text}\n"
        f"Учасників: {len(participants)}\n"
        f"Переможців: {len(winners)}/{giveaway['winners_count']}\n"
        f"Статус: {giveaway['status']}"
    )
    
    if msg.from_user.id in ADMIN_IDS or msg.from_user.id == giveaway["admin_id"]:
        await msg.answer(text, reply_markup=kb.giveaway_actions(giveaway_id))
    else:
        await msg.answer(text)


@router.callback_query(F.data.startswith("stats_"))
async def show_stats(callback: CallbackQuery):
    giveaway_id = callback.data.replace("stats_", "")
    giveaway = storage.get_giveaway(giveaway_id)
    
    if not giveaway:
        await callback.answer("❌ Розіграш не знайдено", show_alert=True)
        return
    
    participants = storage.get_participants(giveaway_id)
    winners = storage.get_winners(giveaway_id)
    
    text = (
        f"📊 Статистика розіграшу {giveaway_id}\n\n"
        f"Всього учасників: {len(participants)}\n"
        f"Вибрано переможців: {len(winners)}/{giveaway['winners_count']}\n\n"
    )
    
    if participants:
        text += "Учасники:\n" + "\n".join(f"• @{p}" for p in participants[:20])
        if len(participants) > 20:
            text += f"\n... та ще {len(participants) - 20}"
    
    await callback.message.edit_text(text, reply_markup=kb.giveaway_actions(giveaway_id))
    await callback.answer()


@router.callback_query(F.data.startswith("delete_"))
async def delete_giveaway(callback: CallbackQuery):
    giveaway_id = callback.data.replace("delete_", "")
    giveaway = storage.get_giveaway(giveaway_id)
    
    if not giveaway:
        await callback.answer("❌ Розіграш не знайдено", show_alert=True)
        return
    
    if callback.from_user.id != giveaway["admin_id"]:
        await callback.answer("❌ Ви не можете видалити цей розіграш", show_alert=True)
        return
    
    storage.delete_giveaway(giveaway_id)
    await callback.message.edit_text(f"✅ Розіграш {giveaway_id} видалено")
    await callback.answer()
