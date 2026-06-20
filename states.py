from aiogram.fsm.state import State, StatesGroup


class UserAccount(StatesGroup):
    session_name = State()
    api_id = State()
    api_hash = State()
    phone = State()
    code = State()
    password = State()


class GiveawayCreate(StatesGroup):
    mode = State()
    text = State()
    button_text = State()
    channels = State()
    winners_count = State()
    publish_channel = State()


class GiveawayManual(StatesGroup):
    giveaway_id = State()
    username = State()


class GiveawayDraw(StatesGroup):
    giveaway_id = State()
    confirm = State()


class MessageBroadcast(StatesGroup):
    giveaway_id = State()
    message = State()
