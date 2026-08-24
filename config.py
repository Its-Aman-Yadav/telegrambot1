import os
import sys
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()
CHANNEL_INVITE_LINK = os.getenv("CHANNEL_INVITE_LINK", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "0").strip()
DB_NAME = os.getenv("DB_NAME", "movies_bot.db").strip()

try:
    ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW else 0
except ValueError:
    ADMIN_ID = 0

# If invite link is missing but CHANNEL_ID starts with @, construct it
if not CHANNEL_INVITE_LINK and CHANNEL_ID.startswith("@"):
    CHANNEL_INVITE_LINK = f"https://t.me/{CHANNEL_ID.lstrip('@')}"

def validate_config():
    """Validates if essential configuration variables are set."""
    errors = []
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        errors.append("BOT_TOKEN is missing or set to placeholder. Please set BOT_TOKEN in .env")
    if not CHANNEL_ID or CHANNEL_ID == "@YourChannelUsername":
        errors.append("CHANNEL_ID is missing or set to placeholder. Please set CHANNEL_ID in .env")
    if not CHANNEL_INVITE_LINK:
        errors.append("CHANNEL_INVITE_LINK is missing. Please set CHANNEL_INVITE_LINK in .env")
    return errors
