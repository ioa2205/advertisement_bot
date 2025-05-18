import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_CHAT_ID_STR = os.environ.get("TARGET_CHAT_ID") # Get as string first

# Attempt to convert TARGET_CHAT_ID to int if it's purely numeric (for user IDs)
# If it starts with @, it's a channel username and should remain a string.
if TARGET_CHAT_ID_STR and TARGET_CHAT_ID_STR.startswith('@'):
    TARGET_CHAT_ID = TARGET_CHAT_ID_STR
elif TARGET_CHAT_ID_STR:
    try:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID_STR)
    except ValueError:
        TARGET_CHAT_ID = TARGET_CHAT_ID_STR # Keep as string if not purely numeric (e.g. channel username without @)
else:
    TARGET_CHAT_ID = None # Or some default if critical and not set

IS_CHANNEL_STR = os.environ.get("IS_CHANNEL", "True") # Default to True if not set
IS_CHANNEL = IS_CHANNEL_STR.lower() == 'true'

DATABASE_NAME = "ads_bot.db"
DEFAULT_LANGUAGE = 'uz'
SUPPORTED_LANGUAGES = {
    'en': '🇬🇧 English',
    'ru': '🇷🇺 Русский',
    'uz': '🇺🇿 Uzbek'
}
MAX_MEDIA_ITEMS = 10
MAX_DESCRIPTION_LENGTH = 1000 # Characters
CONVERSATION_TIMEOUT_DURATION = 60 * 30  # 30 minutes

# Category keys (used internally and for localization keys)
CATEGORIES_KEYS = {
    "cars": "cars",
    "houses": "houses",
    "animals": "animals",
    "other": "other"
}