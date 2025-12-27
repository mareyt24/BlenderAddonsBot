import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_FILE = "blender_addon_bot.db"
ADMIN_IDS = []  


