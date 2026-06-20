from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def admin_main():
    kb = [
        [KeyboardButton(text="🎁 Створити розіграш")],
        [KeyboardButton(text="📋 Мої розіграші")],
        [KeyboardButton(text="➕ Додати user-акаунт"), KeyboardButton(text="🗑 Видалити акаунт")],
        [KeyboardButton(text="📱 Мої акаунти")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def user_main():
    kb = [
        [KeyboardButton(text="📋 Мої розіграші")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def cancel():
    kb = [[KeyboardButton(text="❌ Скасувати")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def giveaway_mode():
    kb = [
        [InlineKeyboardButton(text="🤖 Через бота", callback_data="mode_bot")],
        [InlineKeyboardButton(text="👤 Через user-акаунт", callback_data="mode_user")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def giveaway_actions(giveaway_id: str):
    kb = [
        [InlineKeyboardButton(text="➕ Додати учасника", callback_data=f"add_participant_{giveaway_id}")],
        [InlineKeyboardButton(text="🎲 Вибрати переможців", callback_data=f"draw_{giveaway_id}")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data=f"stats_{giveaway_id}")],
        [InlineKeyboardButton(text="✉️ Розіслати повідомлення", callback_data=f"broadcast_{giveaway_id}")],
        [InlineKeyboardButton(text="🗑 Видалити розіграш", callback_data=f"delete_{giveaway_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def confirm_draw():
    kb = [
        [InlineKeyboardButton(text="✅ Підтвердити", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="confirm_no")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def participate_button():
    kb = [[InlineKeyboardButton(text="Взяти участь", callback_data="participate")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def skip_channels():
    kb = [[InlineKeyboardButton(text="⏭ Пропустити", callback_data="skip_channels")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def finish_channels():
    kb = [[InlineKeyboardButton(text="✅ Завершити", callback_data="finish_channels")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)
