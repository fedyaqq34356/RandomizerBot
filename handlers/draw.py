from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from storage import storage
from states import GiveawayDraw
import keyboards as kb

router = Router()


@router.callback_query(F.data.startswith("draw_"))
async def draw_winners_start(callback: CallbackQuery, state: FSMContext):
    giveaway_id = callback.data.replace("draw_", "")
    giveaway = storage.get_giveaway(giveaway_id)
    
    if not giveaway:
        await callback.answer("❌ Розіграш не знайдено", show_alert=True)
        return
    
    if callback.from_user.id != giveaway["admin_id"]:
        await callback.answer("❌ Ви не можете вибирати переможців", show_alert=True)
        return
    
    participants = storage.get_participants(giveaway_id)
    
    if not participants:
        await callback.answer("❌ Немає учасників для розіграшу", show_alert=True)
        return
    
    if len(participants) < giveaway["winners_count"]:
        await callback.answer(
            f"⚠️ Учасників ({len(participants)}) менше ніж переможців ({giveaway['winners_count']})",
            show_alert=True
        )
        return
    
    existing_winners = storage.get_winners(giveaway_id)
    if existing_winners:
        await callback.message.edit_text(
            f"⚠️ Переможці вже обрані!\n\n"
            f"Поточні переможці:\n" + "\n".join(f"• @{w}" for w in existing_winners) + "\n\n"
            f"Обрати нових переможців?",
            reply_markup=kb.confirm_draw()
        )
    else:
        await callback.message.edit_text(
            f"Розіграш {giveaway_id}\n"
            f"Учасників: {len(participants)}\n"
            f"Буде обрано переможців: {giveaway['winners_count']}\n\n"
            f"Підтвердити?",
            reply_markup=kb.confirm_draw()
        )
    
    await state.update_data(giveaway_id=giveaway_id)
    await state.set_state(GiveawayDraw.confirm)
    await callback.answer()


@router.callback_query(F.data == "confirm_yes", GiveawayDraw.confirm)
async def confirm_draw(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    giveaway_id = data["giveaway_id"]
    
    giveaway = storage.get_giveaway(giveaway_id)
    if not giveaway:
        await callback.answer("❌ Розіграш не знайдено", show_alert=True)
        await state.clear()
        return
    
    winners = storage.draw_winners(giveaway_id)
    
    await state.clear()
    
    winners_text = "\n".join(f"🏆 @{w}" for w in winners)
    
    await callback.message.edit_text(
        f"🎉 Переможці обрані!\n\n"
        f"Розіграш: {giveaway_id}\n"
        f"Переможців: {len(winners)}\n\n"
        f"{winners_text}",
        reply_markup=kb.giveaway_actions(giveaway_id)
    )
    await callback.answer("✅ Переможців обрано!")


@router.callback_query(F.data == "confirm_no", GiveawayDraw.confirm)
async def cancel_draw(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    giveaway_id = data["giveaway_id"]
    
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Вибір переможців скасовано",
        reply_markup=kb.giveaway_actions(giveaway_id)
    )
    await callback.answer()
