from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from pathlib import Path
from config import ADMIN_IDS
from storage import storage
from states import UserAccount
import keyboards as kb
import auth

router = Router()


@router.message(F.text == "➕ Додати user-акаунт")
async def add_account_start(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(UserAccount.session_name)
    await msg.answer("Введіть ім'я акаунта:", reply_markup=kb.cancel())


@router.message(UserAccount.session_name)
async def add_session_name(msg: Message, state: FSMContext):
    if msg.text == "❌ Скасувати":
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    await state.update_data(session_name=msg.text)
    await state.set_state(UserAccount.api_id)
    await msg.answer("Введіть API ID:")


@router.message(UserAccount.api_id)
async def add_api_id(msg: Message, state: FSMContext):
    if msg.text == "❌ Скасувати":
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    try:
        api_id = int(msg.text)
        await state.update_data(api_id=api_id)
        await state.set_state(UserAccount.api_hash)
        await msg.answer("Введіть API Hash:")
    except ValueError:
        await msg.answer("Невірний формат. Введіть число:")


@router.message(UserAccount.api_hash)
async def add_api_hash(msg: Message, state: FSMContext):
    if msg.text == "❌ Скасувати":
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    await state.update_data(api_hash=msg.text)
    await state.set_state(UserAccount.phone)
    await msg.answer("Введіть номер телефону (+380...):")


@router.message(UserAccount.phone)
async def add_phone(msg: Message, state: FSMContext):
    if msg.text == "❌ Скасувати":
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    data = await state.get_data()
    
    success, result = await auth.start(
        msg.from_user.id,
        data["session_name"],
        data["api_id"],
        data["api_hash"],
        msg.text
    )
    
    if success:
        await state.set_state(UserAccount.code)
        await msg.answer(f"{result}. Введіть код:")
    else:
        await state.clear()
        await msg.answer(f"Помилка: {result}", reply_markup=kb.admin_main())


@router.message(UserAccount.code)
async def add_code(msg: Message, state: FSMContext):
    if msg.text == "❌ Скасувати":
        await auth.cancel(msg.from_user.id)
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    code = msg.text.replace(" ", "")
    status, result = await auth.verify_code(msg.from_user.id, code)
    
    if status == "2fa":
        await state.set_state(UserAccount.password)
        await msg.answer(result)
    elif status == "retry":
        await msg.answer(result)
    elif status:
        await state.clear()
        await msg.answer(result, reply_markup=kb.admin_main())
    else:
        await state.clear()
        await msg.answer(f"Помилка: {result}", reply_markup=kb.admin_main())


@router.message(UserAccount.password)
async def add_password(msg: Message, state: FSMContext):
    if msg.text == "❌ Скасувати":
        await auth.cancel(msg.from_user.id)
        await state.clear()
        await msg.answer("Скасовано", reply_markup=kb.admin_main())
        return
    
    success, result = await auth.verify_password(msg.from_user.id, msg.text)
    await state.clear()
    
    if success:
        await msg.answer(result, reply_markup=kb.admin_main())
    else:
        await msg.answer(f"Помилка: {result}", reply_markup=kb.admin_main())


@router.message(F.text == "📱 Мої акаунти")
async def list_accounts(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    accounts = storage.get_user_accounts(msg.from_user.id)
    
    if not accounts:
        await msg.answer("У вас немає доданих акаунтів")
        return
    
    text = "Ваші user-акаунти:\n\n"
    for i, (name, data) in enumerate(accounts.items(), 1):
        text += f"{i}. {name} ({data['phone']})\n"
    
    await msg.answer(text)


@router.message(F.text == "🗑 Видалити акаунт")
async def delete_account_start(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    accounts = storage.get_user_accounts(msg.from_user.id)
    
    if not accounts:
        await msg.answer("У вас немає доданих акаунтів")
        return
    
    text = "Виберіть акаунт для видалення:\n\n"
    for i, (name, data) in enumerate(accounts.items(), 1):
        text += f"{i}. {name} ({data['phone']})\n"
    
    await state.set_state(UserAccount.session_name)
    await msg.answer(text + "\nВведіть номер:", reply_markup=kb.cancel())


@router.message(F.text.regexp(r"^\d+$"))
async def delete_account_confirm(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != UserAccount.session_name or msg.from_user.id not in ADMIN_IDS:
        return
    
    try:
        idx = int(msg.text) - 1
        accounts = storage.get_user_accounts(msg.from_user.id)
        accounts_list = list(accounts.keys())
        
        if 0 <= idx < len(accounts_list):
            name = accounts_list[idx]
            
            session_file = Path(f"sessions/{name}.session")
            if session_file.exists():
                session_file.unlink()
            
            storage.remove_user_account(msg.from_user.id, name)
            await state.clear()
            await msg.answer(f"Видалено: {name}", reply_markup=kb.admin_main())
        else:
            await msg.answer("Невірний номер")
    except ValueError:
        await msg.answer("Введіть номер:")
