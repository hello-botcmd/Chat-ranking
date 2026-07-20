import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = int(os.getenv("OWNER_ID", 0))          # your Telegram user ID
WELCOME_IMAGE_PATH = "assets/welcome.jpg"
BOT_USERNAME = os.getenv("BOT_USERNAME")          # e.g., "MyRankBot"
