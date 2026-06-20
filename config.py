import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

MAX_WINNERS = 100

GIVEAWAY_CONFIG = {
    "min_participants": 1,
    "max_participants": 10000,
    "max_winners": MAX_WINNERS
}
