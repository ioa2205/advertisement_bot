# selling_bot/main.py
import logging
from telegram.ext import Application, CommandHandler
from telegram import BotCommand # For setting command list

import config # Ensure this import works (absolute from project root)
from services import database_service as db
from handlers.conversation_flow import (
    create_ad_posting_conversation_handler,
    create_language_change_conversation_handler,
    # cancel_conversation, # Individual convs have cancel in fallbacks
    help_command
)
from localization import get_text # For command descriptions

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    await db.init_db()
    logger.info("Bot application initialized and database checked/created.")
    
    # Define bot commands for the '/' menu (optional but good UX)
    # Ensure you have localization keys for these descriptions
    commands_to_set = [
        BotCommand("start", get_text("command_desc_start", config.DEFAULT_LANGUAGE) if "command_desc_start" in strings[config.DEFAULT_LANGUAGE] else "Create a new ad"),
        BotCommand("language", get_text("command_desc_language", config.DEFAULT_LANGUAGE) if "command_desc_language" in strings[config.DEFAULT_LANGUAGE] else "Change language"),
        BotCommand("help", get_text("command_desc_help", config.DEFAULT_LANGUAGE) if "command_desc_help" in strings[config.DEFAULT_LANGUAGE] else "Get help"),
        BotCommand("cancel", get_text("command_desc_cancel", config.DEFAULT_LANGUAGE) if "command_desc_cancel" in strings[config.DEFAULT_LANGUAGE] else "Cancel current operation")
    ]
    # You'd need to add these "command_desc_..." keys to your localization.py strings
    # Example for localization.py:
    # 'en': { ..., "command_desc_start": "Start creating a new ad", ... }
    try:
        await application.bot.set_my_commands(commands_to_set)
        logger.info("Bot commands set successfully.")
    except Exception as e:
        logger.error(f"Failed to set bot commands: {e}")


def main() -> None:
    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("BOT_TOKEN is not set correctly in config.py.")
        return
    if not config.TARGET_CHAT_ID or config.TARGET_CHAT_ID == "YOUR_TARGET_CHAT_ID":
        logger.error("TARGET_CHAT_ID is not set correctly in config.py.")
        return

    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()

    ad_posting_conv_handler = create_ad_posting_conversation_handler()
    language_change_conv_handler = create_language_change_conversation_handler()

    application.add_handler(ad_posting_conv_handler)
    application.add_handler(language_change_conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    # A top-level cancel might be useful if a user gets stuck outside a known conversation
    # but ConversationHandler's fallbacks should usually catch it.
    # application.add_handler(CommandHandler("cancel", top_level_cancel_function)) # If needed

    logger.info("Bot starting to poll...")
    application.run_polling()

# Need to import strings from localization for set_my_commands
from localization import strings 

if __name__ == "__main__":
    main()