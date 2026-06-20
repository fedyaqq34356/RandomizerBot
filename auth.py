import random
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from storage import storage

DEVICE_MODELS = [
    "Samsung Galaxy S21",
    "iPhone 13 Pro",
    "Xiaomi Mi 11",
    "OnePlus 9 Pro",
    "Google Pixel 6",
    "Huawei P40",
    "Sony Xperia 5 II",
    "Oppo Find X3",
    "Vivo X60 Pro",
    "Realme GT",
    "Asus ROG Phone 5",
    "Nokia 8.3 5G"
]

SYSTEM_VERSIONS = [
    "Android 11",
    "Android 12",
    "Android 13",
    "iOS 15.4",
    "iOS 16.0",
    "iOS 16.3",
    "MIUI 13",
    "One UI 4.1",
    "ColorOS 12"
]

APP_VERSIONS = [
    "8.9.3",
    "9.0.1",
    "9.1.5",
    "9.2.0"
]

sessions_dir = Path("sessions")
sessions_dir.mkdir(exist_ok=True)

active_clients = {}
pending_auth = {}


async def start(admin_id: int, session_name: str, api_id: int, api_hash: str, phone: str):
    try:
        session_path = sessions_dir / f"{session_name}.session"
        
        device_model = random.choice(DEVICE_MODELS)
        system_version = random.choice(SYSTEM_VERSIONS)
        app_version = random.choice(APP_VERSIONS)
        
        client = TelegramClient(
            str(session_path),
            api_id,
            api_hash,
            device_model=device_model,
            system_version=system_version,
            app_version=app_version
        )
        
        await client.connect()
        
        if not await client.is_user_authorized():
            sent_code = await client.send_code_request(phone)
            
            pending_auth[admin_id] = {
                "client": client,
                "phone": phone,
                "phone_code_hash": sent_code.phone_code_hash,
                "session_name": session_name,
                "api_id": api_id,
                "api_hash": api_hash
            }
            
            return True, "Код відправлено"
        else:
            storage.add_user_account(admin_id, session_name, phone, api_id, api_hash)
            await client.disconnect()
            return True, "Акаунт вже авторизовано"
            
    except Exception as e:
        return False, str(e)


async def verify_code(admin_id: int, code: str):
    if admin_id not in pending_auth:
        return False, "Спочатку почніть авторизацію"
    
    try:
        auth_data = pending_auth[admin_id]
        client = auth_data["client"]
        
        await client.sign_in(
            auth_data["phone"],
            code,
            phone_code_hash=auth_data["phone_code_hash"]
        )
        
        storage.add_user_account(
            admin_id,
            auth_data["session_name"],
            auth_data["phone"],
            auth_data["api_id"],
            auth_data["api_hash"]
        )
        
        await client.disconnect()
        del pending_auth[admin_id]
        
        return True, "✅ Акаунт успішно додано"
        
    except SessionPasswordNeededError:
        return "2fa", "Введіть пароль двофакторної аутентифікації:"
        
    except PhoneCodeInvalidError:
        return "retry", "❌ Невірний код. Спробуйте ще раз:"
        
    except Exception as e:
        return False, str(e)


async def verify_password(admin_id: int, password: str):
    if admin_id not in pending_auth:
        return False, "Спочатку почніть авторизацію"
    
    try:
        auth_data = pending_auth[admin_id]
        client = auth_data["client"]
        
        await client.sign_in(password=password)
        
        storage.add_user_account(
            admin_id,
            auth_data["session_name"],
            auth_data["phone"],
            auth_data["api_id"],
            auth_data["api_hash"]
        )
        
        await client.disconnect()
        del pending_auth[admin_id]
        
        return True, "✅ Акаунт успішно додано"
        
    except Exception as e:
        return False, str(e)


async def cancel(admin_id: int):
    if admin_id in pending_auth:
        client = pending_auth[admin_id]["client"]
        await client.disconnect()
        del pending_auth[admin_id]


async def get_client(admin_id: int, session_name: str):
    accounts = storage.get_user_accounts(admin_id)
    
    if session_name not in accounts:
        return None
    
    if session_name in active_clients:
        return active_clients[session_name]
    
    account = accounts[session_name]
    session_path = sessions_dir / f"{session_name}.session"
    
    client = TelegramClient(
        str(session_path),
        account["api_id"],
        account["api_hash"]
    )
    
    await client.connect()
    
    if await client.is_user_authorized():
        active_clients[session_name] = client
        return client
    
    await client.disconnect()
    return None


async def disconnect_client(session_name: str):
    if session_name in active_clients:
        await active_clients[session_name].disconnect()
        del active_clients[session_name]
