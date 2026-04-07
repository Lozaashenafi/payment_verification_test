import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LEUL_API_KEY = os.getenv("LEUL_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Convert the comma-separated string of manager IDs into a list of integers
manager_ids_str = os.getenv("MANAGER_TG_IDS", "")
MANAGER_IDS = [int(id.strip()) for id in manager_ids_str.split(",") if id.strip().isdigit()]

BASE_API_URL = 'https://verifyapi.leulzenebe.pro'