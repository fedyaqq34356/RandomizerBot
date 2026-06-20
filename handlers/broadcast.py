from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from storage import storage
from states import MessageBroadcast
import keyboards as kb
import auth

router = Router()


@router.callback_query(F.data.startswith("broadcast_"))
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    giveaway_id = callback.data.replace("broadcast_", "")
    giveaway = storage.get_giveaway(giveaway_id)
    
    if not giveaway:
        await callback.answer("❌ Розіграш не знайдено", show_alert=True)
        return
    
    if callback.from_user.id != giveaway["admin_id"]:
        await callback.answer("❌ Ви не можете робити розсилку", show_alert=True)
        return
    
    winners = storage.get_winners(giveaway_id)
    
    if not winners:
        await callback.answer("❌ Спочатку виберіть переможців", show_alert=True)
        return
    
    await state.update_data(giveaway_id=giveaway_id)
    await state.set_state(MessageBroadcast.message)
    
    await callback.message.edit_text(
        f"Розсилка для розіграшу {giveaway_id}\n"
        f"Переможців: {len(winners)}\n\n"
        "Введіть повідомлення для розсилки:"
    )
    await callback.answer()


@router.message(MessageBroadcast.message)
async def broadcast_send(msg: Message, state: FSMContext, bot: Bot):
    if msg.text == "❌ Скасувати":
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    data = await state.get_data()
    giveaway_id = data["giveaway_id"]
    
    giveaway = storage.get_giveaway(giveaway_id)
    if not giveaway:
        await msg.answer("❌ Розіграш не знайдено", reply_markup=kb.admin_main())
        await state.clear()
        return
    
    winners = storage.get_winners(giveaway_id)
    message_text = msg.text
    
    success_count = 0
    fail_count = 0
    
    if giveaway["mode"] == "bot":
        status_msg = await msg.answer(f"📤 Розсилка через бота...\n0/{len(winners)}")
        
        for i, username in enumerate(winners, 1):
            try:
                user = await bot.get_chat(f"@{username}")
                await bot.send_message(user.id, message_text)
                success_count += 1
            except Exception:
                fail_count += 1
            
            if i % 5 == 0 or i == len(winners):
                await status_msg.edit_text(f"📤 Розсилка...\n{i}/{len(winners)}")
        
        await status_msg.edit_text(
            f"✅ Розсилка завершена!\n\n"
            f"Відправлено: {success_count}\n"
            f"Не вдалось: {fail_count}",
            reply_markup=kb.admin_main()
        )
        
    else:
        accounts = storage.get_user_accounts(msg.from_user.id)
        
        if not accounts:
            await msg.answer("❌ Немає доданих user-акаунтів", reply_markup=kb.admin_main())
            await state.clear()
            return
        
        account_name = list(accounts.keys())[0]
        client = await auth.get_client(msg.from_user.id, account_name)
        
        if not client:
            await msg.answer("❌ Не вдалось підключитись до акаунта", reply_markup=kb.admin_main())
            await state.clear()
            return
        
        status_msg = await msg.answer(f"📤 Розсилка через user-акаунт...\n0/{len(winners)}")
        
        for i, username in enumerate(winners, 1):
            try:
                await client.send_message(username, message_text)
                success_count += 1
            except Exception:
                fail_count += 1
            
            if i % 5 == 0 or i == len(winners):
                await status_msg.edit_text(f"📤 Розсилка...\n{i}/{len(winners)}")
        
        await status_msg.edit_text(
            f"✅ Розсилка завершена!\n\n"
            f"Відправлено: {success_count}\n"
            f"Не вдалось: {fail_count}",
            reply_markup=kb.admin_main()
        )
    
    await state.clear()
