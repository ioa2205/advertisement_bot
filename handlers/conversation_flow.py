# selling_bot/handlers/conversation_flow.py
import logging
import re
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest # For handling message edit errors etc.

import constants
import config
from localization import get_text, get_user_lang, SUPPORTED_LANGUAGES, get_category_display_name
from services import database_service as db
from services import message_formatter

logger = logging.getLogger(__name__)

# --- Helper Functions for Conversation Flow ---
def get_common_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data.setdefault('user_id', user.id)
    context.user_data.setdefault('first_name', user.first_name)
    context.user_data.setdefault('username', user.username)
    if 'lang' not in context.user_data:
        pref_lang = context.user_data.get('db_pref_lang')
        context.user_data['lang'] = pref_lang if pref_lang and pref_lang in SUPPORTED_LANGUAGES else config.DEFAULT_LANGUAGE
    context.user_data.setdefault(constants.CAT_SPECIFIC_DATA_KEY, {})
    context.user_data.setdefault('media_files', [])


async def clear_user_data_for_new_post(context: ContextTypes.DEFAULT_TYPE):
    # Keys to keep across a full reset triggered by /start or /cancel
    preserved_keys = ['lang', 'user_id', 'first_name', 'username', 'db_pref_lang']
    
    data_to_preserve = {}
    for key in preserved_keys:
        if key in context.user_data:
            data_to_preserve[key] = context.user_data[key]

    # Log what's being preserved and what's in user_data before clearing
    # logger.debug(f"Before clear_user_data: {context.user_data}")
    # logger.debug(f"Data to preserve: {data_to_preserve}")

    context.user_data.clear() # Clear everything
    context.user_data.update(data_to_preserve) # Add back preserved items

    # Re-initialize keys that should always exist for a new post flow
    context.user_data['media_files'] = []
    context.user_data[constants.CAT_SPECIFIC_DATA_KEY] = {}


async def _ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question_key: str, next_state: int,
                        is_optional: bool = False, optional_field_key: str = None,
                        reply_markup_override: InlineKeyboardMarkup = None, **kwargs) -> int:
    lang = get_user_lang(context)
    text_to_send = get_text(question_key, lang, **kwargs)
    
    current_reply_markup = reply_markup_override
    if not current_reply_markup and is_optional and optional_field_key:
        keyboard = [[InlineKeyboardButton(get_text("btn_skip", lang),
                                          callback_data=f"{constants.SKIP_FIELD_CALLBACK_PREFIX}{optional_field_key}")]]
        current_reply_markup = InlineKeyboardMarkup(keyboard)
    elif not current_reply_markup and question_key == "ask_description":
         keyboard = [[InlineKeyboardButton(get_text("btn_skip_description", lang),
                                          callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_SKIP_DESCRIPTION}")]]
         current_reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            # Try to edit the message that the callback query originated from
            await update.callback_query.edit_message_text(text_to_send, reply_markup=current_reply_markup, parse_mode=ParseMode.MARKDOWN)
        except BadRequest as e: # e.g. message not modified, or trying to edit media caption as text
            logger.warning(f"Failed to edit message for callback query: {e}. Sending new message.")
            await context.bot.send_message(update.effective_chat.id, text_to_send, reply_markup=current_reply_markup, parse_mode=ParseMode.MARKDOWN)
    elif update.message:
        await update.message.reply_text(text_to_send, reply_markup=current_reply_markup, parse_mode=ParseMode.MARKDOWN)
    return next_state


async def _handle_skip_field(update: Update, context: ContextTypes.DEFAULT_TYPE, next_state_func, **next_state_args) -> int:
    query = update.callback_query
    await query.answer()
    field_key_to_skip = query.data.split(constants.SKIP_FIELD_CALLBACK_PREFIX)[1]
    lang = get_user_lang(context)
    context.user_data[constants.CAT_SPECIFIC_DATA_KEY][field_key_to_skip] = None # Or some other indicator like "SKIPPED"
    
    field_name_for_message = field_key_to_skip.replace("_", " ").title()
    
    # We need to edit the message AFTER calling next_state_func if next_state_func sends a new message.
    # So, next_state_func should handle the message sending/editing for its prompt.
    # This handler just updates user_data and calls the next step.
    # The _ask_question called by next_state_func will edit the message.
    # We can send a small confirmation if needed, or let the next prompt replace this message.
    # For now, let the _ask_question in next_state_func handle the message update.
    logger.info(f"User {update.effective_user.id} skipped field: {field_key_to_skip}")
    # await query.edit_message_text(get_text("field_skipped", lang, field_name=field_name_for_message)) # This might get overwritten

    return await next_state_func(update, context, **next_state_args)


async def _handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE, field_key: str, 
                             next_state_func, current_state_for_reask: int, **next_state_args) -> int:
    text = update.message.text.strip()
    lang = get_user_lang(context)
    if not text:
        await update.message.reply_text(get_text("invalid_input", lang) + " This field cannot be empty.")
        return current_state_for_reask
        
    context.user_data[constants.CAT_SPECIFIC_DATA_KEY][field_key] = text # For specific fields
    logger.info(f"User {update.effective_user.id} entered {field_key}: {text[:50]}")
    
    if context.user_data.get('editing_field') == field_key:
        context.user_data.pop('editing_field') # Consume the flag
        logger.info(f"Finished editing field {field_key}, returning to preview.")
        return await show_preview(update, context) 
        
    return await next_state_func(update, context, **next_state_args)


# --- Start, Language (Initial & Change), Help, Cancel, Timeout ---
# selling_bot/handlers/conversation_flow.py

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Log the current conversation state for this user, if available
    # This is a bit of a hack to peek into ConversationHandler's state
    # conv_key = (chat_id, user.id) # Assuming per_user=True, per_chat=True
    # current_conv_state = context.application._conversation_handlers[0].conversations.get(conv_key) # Assuming handler index 0
    # logger.info(f"--- /start called by user {user.id}. Current internal conv state: {current_conv_state} ---")
    # logger.info(f"Current user_data BEFORE any action: {context.user_data}")

    get_common_data(update, context) # Ensure user_data basic structure

    # Check if an ad flow is considered active based on our user_data keys
    is_in_ad_flow = bool(context.user_data.get('category') or \
                         (context.user_data.get(constants.CAT_SPECIFIC_DATA_KEY) and \
                          len(context.user_data.get(constants.CAT_SPECIFIC_DATA_KEY, {})) > 0))

    if is_in_ad_flow:
        logger.info(f"User {user.id} used /start during an active ad flow. Explicitly resetting.")
        lang_for_reset_message = get_user_lang(context)
        await update.message.reply_text(get_text("conversation_restarted", lang_for_reset_message))
        
        # Perform full cleanup
        await clear_user_data_for_new_post(context)
        
        # Explicitly tell the ConversationHandler that the *current* interaction path for this update should end.
        # This is a signal that if this /start was processed *within* an existing conversation
        # (e.g., if /start was also a fallback or a state handler), that path ends.
        # Since /start is an entry point, the handler will then re-evaluate it as a new entry.
        # However, returning ConversationHandler.END from an entry_point handler might prevent
        # it from re-entering. This is the tricky part.

        # The most reliable way if an entry_point itself needs to reset is that
        # the ConversationHandler must be designed to allow re-entry on its entry_points,
        # and the state must be cleaned from user_data.

    # Always clear user_data to ensure a fresh start, regardless of the check above.
    # This makes the is_in_ad_flow check mostly for user messaging.
    await clear_user_data_for_new_post(context)
    # logger.info(f"user_data AFTER clear_user_data_for_new_post: {context.user_data}")

    # Proceed to ask for language or category
    pref_lang = await db.get_user_pref_lang(user.id)
    # Re-populate lang in user_data after clear, as clear_user_data_for_new_post preserves it from db_pref_lang
    if pref_lang and pref_lang in SUPPORTED_LANGUAGES:
        context.user_data['lang'] = pref_lang
        context.user_data['db_pref_lang'] = pref_lang
        logger.info(f"User {user.id} starting/restarting. Loaded lang {pref_lang} from DB.")
        return await ask_category(update, context) # Will send its own message

    logger.info(f"User {user.id} starting/restarting. Asking for language.")
    keyboard = [[InlineKeyboardButton(text, callback_data=f"{constants.LANG_CALLBACK_PREFIX}{code}")]
                for code, text in SUPPORTED_LANGUAGES.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        get_text("welcome", config.DEFAULT_LANGUAGE, name=user.first_name),
        reply_markup=reply_markup
    )
    return constants.LANG_SELECT


async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: # Initial selection
    query = update.callback_query
    await query.answer()
    lang_code = query.data.split(constants.LANG_CALLBACK_PREFIX)[1]

    if lang_code not in SUPPORTED_LANGUAGES:
        logger.warning(f"Invalid language code selected: {lang_code}")
        await query.edit_message_text(get_text("general_error", context.user_data.get('lang', config.DEFAULT_LANGUAGE)))
        return ConversationHandler.END

    context.user_data['lang'] = lang_code
    user = update.effective_user
    await db.set_user_pref_lang(user.id, lang_code, user.first_name, user.username)
    
    logger.info(f"User {user.id} selected language: {lang_code}")
    # Message will be edited by ask_category
    # await query.edit_message_text(get_text("lang_chosen", lang_code)) 
    return await ask_category(update, context)

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    get_common_data(update, context)
    user = update.effective_user
    lang = get_user_lang(context)
    logger.info(f"User {user.id} initiated language change. Current lang: {lang}")

    if context.user_data.get('category') or context.user_data.get(constants.CAT_SPECIFIC_DATA_KEY):
        context.user_data['_interrupted_ad_flow'] = True
    
    keyboard = [[InlineKeyboardButton(text, callback_data=f"{constants.LANG_CALLBACK_PREFIX}change_{code}")]
                for code, text in SUPPORTED_LANGUAGES.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text("change_language_prompt", lang), reply_markup=reply_markup)
    return constants.CHANGE_LANG_PROMPT

async def handle_language_change_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang_code = query.data.split(f"{constants.LANG_CALLBACK_PREFIX}change_")[1]

    if lang_code not in SUPPORTED_LANGUAGES:
        logger.warning(f"Invalid language code selected during change: {lang_code}")
        await query.edit_message_text(get_text("general_error", context.user_data.get('lang', config.DEFAULT_LANGUAGE)))
        return ConversationHandler.END 

    old_lang = context.user_data.get('lang', config.DEFAULT_LANGUAGE)
    context.user_data['lang'] = lang_code
    user = update.effective_user
    await db.set_user_pref_lang(user.id, lang_code, user.first_name, user.username)
    
    new_lang_display = SUPPORTED_LANGUAGES.get(lang_code, lang_code)
    logger.info(f"User {user.id} changed language from {old_lang} to {lang_code}")

    if context.user_data.pop('_interrupted_ad_flow', False):
        await query.edit_message_text(get_text("language_changed_success", lang_code, new_lang_display=new_lang_display))
        # Clear ad-specific data more thoroughly
        ad_keys_to_clear = ['category', 'price', 'location', 'description', 
                            'editing_field', 'last_preview_message_id', 'media_edited_flag']
        for key in ad_keys_to_clear:
            context.user_data.pop(key, None)
        context.user_data[constants.CAT_SPECIFIC_DATA_KEY] = {}
        context.user_data['media_files'] = []
    else:
        await query.edit_message_text(get_text("lang_chosen", lang_code))
    return ConversationHandler.END
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    get_common_data(update, context)
    lang = get_user_lang(context)
    await update.message.reply_text(get_text("help_message", lang), parse_mode=ParseMode.MARKDOWN)

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    get_common_data(update, context) # Ensure lang is available for get_text
    lang = get_user_lang(context)
    logger.info(f"User {user.id} cancelled the conversation.")
    context.user_data.pop('_interrupted_ad_flow', None) # Clear interruption flag

    reply_text = get_text("post_cancelled", lang)
    if update.message:
        await update.message.reply_text(reply_text)
    elif update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(reply_text)
        except BadRequest: # Message might not be editable (e.g., too old, or no text part)
             await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text)
    
    await clear_user_data_for_new_post(context)
    return ConversationHandler.END

async def timeout_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data.get('user_id', 'Unknown user')
    lang = get_user_lang(context) # Get lang before clearing
    logger.info(f"Conversation with user {user_id} timed out.")
    
    chat_id = context.user_data.get('_chat_id_for_timeout') 
    if not chat_id and update.effective_chat:
        chat_id = update.effective_chat.id
    
    if chat_id:
        await context.bot.send_message(chat_id, get_text("timeout_message", lang))
    
    await clear_user_data_for_new_post(context)
    return ConversationHandler.END

# --- Category Selection & Branching ---
async def ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    get_common_data(update, context)
    lang = get_user_lang(context)
    keyboard = [[InlineKeyboardButton(get_category_display_name(key, lang), 
                                      callback_data=f"{constants.CATEGORY_CALLBACK_PREFIX}{key}")]
                for key in config.CATEGORIES_KEYS.values()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    prompt_text = get_text("choose_category", lang)

    if update.callback_query: # Typically from initial language selection
        # Edit the "Language set to X" message
        await update.callback_query.edit_message_text(prompt_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    elif update.message: # From /start if lang was pre-loaded
        await update.message.reply_text(prompt_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    return constants.CATEGORY_SELECT

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query # This handler is always from a callback
    # await query.answer() # Answered by _ask_question if it edits
    category_key = query.data.split(constants.CATEGORY_CALLBACK_PREFIX)[1]
    
    if category_key not in config.CATEGORIES_KEYS.values():
        logger.warning(f"Invalid category key selected: {category_key}")
        await query.edit_message_text(get_text("general_error", get_user_lang(context)))
        return ConversationHandler.END

    get_common_data(update, context) # Ensure user_data structures are ready
    context.user_data['category'] = category_key
    context.user_data[constants.CAT_SPECIFIC_DATA_KEY] = {} # Initialize/reset specific data for new category
    lang = get_user_lang(context)
    
    logger.info(f"User {update.effective_user.id} selected category: {category_key}")

    # The _ask_question will edit the "Choose category..." message.
    if category_key == config.CATEGORIES_KEYS["cars"]:
        # Send "Category chosen" message first as context before the first question.
        await query.edit_message_text(get_text("category_chosen_cars", lang))
        return await _ask_question(update, context, "ask_car_make_model", constants.CAR_MAKE_MODEL)
    elif category_key == config.CATEGORIES_KEYS["houses"]:
        await query.edit_message_text(get_text("category_chosen_houses", lang))
        prop_types = ["apartment", "house", "land", "commercial", "other"]
        keyboard_prop = []
        row = []
        for pt_key in prop_types:
            row.append(InlineKeyboardButton(get_text(f"property_type_{pt_key}", lang), 
                                  callback_data=f"{constants.PROPERTY_TYPE_CALLBACK_PREFIX}{pt_key}"))
            if len(row) == 2: # Max 2 buttons per row
                keyboard_prop.append(row)
                row = []
        if row: keyboard_prop.append(row) # Add remaining buttons

        return await _ask_question(update, context, "ask_house_property_type", 
                                   constants.HOUSE_PROPERTY_TYPE, reply_markup_override=InlineKeyboardMarkup(keyboard_prop))
    elif category_key == config.CATEGORIES_KEYS["animals"]:
        await query.edit_message_text(get_text("category_chosen_animals", lang))
        return await _ask_question(update, context, "ask_animal_type", constants.ANIMAL_TYPE)
    elif category_key == config.CATEGORIES_KEYS["other"]:
        await query.edit_message_text(get_text("category_chosen_other", lang))
        return await _ask_question(update, context, "ask_other_item_name", constants.OTHER_ITEM_NAME)
    
    return ConversationHandler.END

# --- CARS Flow ---
async def handle_car_make_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered handle_car_make_model. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_text_input(update, context, 'car_make_model', 
                                    _ask_question, question_key="ask_car_year", next_state=constants.CAR_YEAR, 
                                    is_optional=True, optional_field_key="car_year", current_state_for_reask=constants.CAR_MAKE_MODEL)

async def handle_car_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered handle_car_year. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_text_input(update, context, 'car_year',
                                    _ask_question, question_key="ask_car_mileage", next_state=constants.CAR_MILEAGE, current_state_for_reask=constants.CAR_YEAR)
async def skip_car_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered skip_car_year. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_skip_field(update, context, 
                                    _ask_question, question_key="ask_car_mileage", next_state=constants.CAR_MILEAGE)

async def handle_car_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered handle_car_mileage. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_text_input(update, context, 'car_mileage', 
                                    _ask_question, question_key="ask_price", next_state=constants.ASK_PRICE, current_state_for_reask=constants.CAR_MILEAGE)

# --- HOUSES Flow ---
async def handle_house_property_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered handle_house_property_type. Editing flag: {context.user_data.get('editing_field')} ---")
    query = update.callback_query
    await query.answer()
    prop_type_key = query.data.split(constants.PROPERTY_TYPE_CALLBACK_PREFIX)[1]
    lang = get_user_lang(context)
    # Store the localized display name for easier preview
    context.user_data[constants.CAT_SPECIFIC_DATA_KEY]['house_property_type'] = get_text(f"property_type_{prop_type_key}", lang)
    logger.info(f"User {update.effective_user.id} selected property type: {prop_type_key}")
    return await _ask_question(update, context, "ask_house_rooms", constants.HOUSE_ROOMS, 
                               is_optional=True, optional_field_key="house_rooms")

async def handle_house_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered handle_house_rooms. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_text_input(update, context, 'house_rooms', 
                                    _ask_question, question_key="ask_house_area", next_state=constants.HOUSE_AREA,
                                    is_optional=True, optional_field_key="house_area", current_state_for_reask=constants.HOUSE_ROOMS)
async def skip_house_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered skip_house_rooms. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_skip_field(update, context, _ask_question, question_key="ask_house_area", 
                                    next_state=constants.HOUSE_AREA, is_optional=True, optional_field_key="house_area")

async def handle_house_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered handle_house_area. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_text_input(update, context, 'house_area', 
                                    _ask_question, question_key="ask_house_year_built", next_state=constants.HOUSE_YEAR_BUILT,
                                    is_optional=True, optional_field_key="house_year_built", current_state_for_reask=constants.HOUSE_AREA)
async def skip_house_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered skip_house_area. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_skip_field(update, context, _ask_question, question_key="ask_house_year_built", 
                                    next_state=constants.HOUSE_YEAR_BUILT, is_optional=True, optional_field_key="house_year_built")

async def handle_house_year_built(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered handle_house_year_built. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_text_input(update, context, 'house_year_built',
                                    _ask_question, question_key="ask_price", next_state=constants.ASK_PRICE, current_state_for_reask=constants.HOUSE_YEAR_BUILT)
async def skip_house_year_built(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered skip_house_year_built. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_skip_field(update, context, _ask_question, question_key="ask_price", next_state=constants.ASK_PRICE)

# --- ANIMALS Flow ---
async def handle_animal_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered handle_animal_type. Editing flag: {context.user_data.get('editing_field')} ---")
    animal_type_text = update.message.text.strip()
    lang = get_user_lang(context)
    if not animal_type_text:
        await update.message.reply_text(get_text("invalid_input", lang) + " Animal type cannot be empty.")
        return constants.ANIMAL_TYPE
    context.user_data[constants.CAT_SPECIFIC_DATA_KEY]['animal_type'] = animal_type_text
    logger.info(f"User {update.effective_user.id} entered animal_type: {animal_type_text}")
    return await _ask_question(update, context, "ask_animal_breed", constants.ANIMAL_BREED,
                               is_optional=True, optional_field_key="animal_breed", 
                               animal_type_placeholder=animal_type_text)

async def handle_animal_breed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered handle_animal_breed. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_text_input(update, context, 'animal_breed',
                                    _ask_question, question_key="ask_animal_age", next_state=constants.ANIMAL_AGE, current_state_for_reask=constants.ANIMAL_BREED)
async def skip_animal_breed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered skip_animal_breed. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_skip_field(update, context, _ask_question, question_key="ask_animal_age", next_state=constants.ANIMAL_AGE)

async def handle_animal_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered handle_animal_age. Editing flag: {context.user_data.get('editing_field')} ---")
    age_text = update.message.text.strip() # This is for age input, not for handling the sex callback
    lang = get_user_lang(context)
    if not age_text: # Or some validation for age
        await update.message.reply_text(get_text("invalid_input", lang) + " Age cannot be empty.")
        return constants.ANIMAL_AGE
    context.user_data[constants.CAT_SPECIFIC_DATA_KEY]['animal_age'] = age_text
    logger.info(f"User {update.effective_user.id} entered animal_age: {age_text}")

    sex_keyboard_buttons = [
        [InlineKeyboardButton(get_text("animal_sex_male", lang), callback_data=f"{constants.ANIMAL_SEX_CALLBACK_PREFIX}male"),
         InlineKeyboardButton(get_text("animal_sex_female", lang), callback_data=f"{constants.ANIMAL_SEX_CALLBACK_PREFIX}female")],
        [InlineKeyboardButton(get_text("btn_skip", lang), callback_data=f"{constants.SKIP_FIELD_CALLBACK_PREFIX}animal_sex")]
    ]
    return await _ask_question(update, context, "ask_animal_sex", constants.ANIMAL_SEX,
                               reply_markup_override=InlineKeyboardMarkup(sex_keyboard_buttons))

async def handle_animal_sex(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: # Callback for sex buttons
    logger.info(f"--- Entered handle_animal_sex. Editing flag: {context.user_data.get('editing_field')} ---")
    query = update.callback_query
    await query.answer()
    sex_choice = query.data.split(constants.ANIMAL_SEX_CALLBACK_PREFIX)[1]
    lang = get_user_lang(context)
    context.user_data[constants.CAT_SPECIFIC_DATA_KEY]['animal_sex'] = get_text(f"animal_sex_{sex_choice}", lang)
    logger.info(f"User {update.effective_user.id} selected animal sex: {sex_choice}")
    return await _ask_question(update, context, "ask_price", constants.ASK_PRICE)

async def skip_animal_sex(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered skip_animal_sex. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_skip_field(update, context, _ask_question, question_key="ask_price", next_state=constants.ASK_PRICE)

# --- OTHER Flow ---
async def handle_other_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"--- Entered handle_other_item_name. Editing flag: {context.user_data.get('editing_field')} ---")
    return await _handle_text_input(update, context, 'other_item_name',
                                    _ask_question, question_key="ask_price", next_state=constants.ASK_PRICE, current_state_for_reask=constants.OTHER_ITEM_NAME)

# --- Common Input Steps Handlers (Price, Location, Description, Media) ---
async def handle_ask_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price = update.message.text.strip()
    lang = get_user_lang(context)
    if not re.search(r'\d', price):
        await update.message.reply_text(get_text("price_invalid", lang))
        return constants.ASK_PRICE
    context.user_data['price'] = price
    logger.info(f"User {update.effective_user.id} entered price: {price}")
    if context.user_data.pop('editing_field', None) == 'price': return await show_preview(update, context)
    return await _ask_question(update, context, "ask_location", constants.ASK_LOCATION)

async def handle_ask_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    location = update.message.text.strip()
    lang = get_user_lang(context)
    if not location:
        await update.message.reply_text(get_text("invalid_input", lang) + " Location cannot be empty.")
        return constants.ASK_LOCATION
    context.user_data['location'] = location
    logger.info(f"User {update.effective_user.id} entered location: {location}")
    if context.user_data.pop('editing_field', None) == 'location': return await show_preview(update, context)
    return await _ask_question(update, context, "ask_description", constants.ASK_DESCRIPTION) # is_optional handled by _ask_question

async def handle_ask_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: # Text input for description
    description = update.message.text.strip()
    lang = get_user_lang(context)
    if len(description) > config.MAX_DESCRIPTION_LENGTH:
        await update.message.reply_text(get_text("description_too_long", lang, max_desc_len=config.MAX_DESCRIPTION_LENGTH))
        return constants.ASK_DESCRIPTION
    context.user_data['description'] = description
    logger.info(f"User {update.effective_user.id} entered description (length: {len(description)}).")
    if context.user_data.pop('editing_field', None) == 'description': return await show_preview(update, context)
    # Prepare keyboard for media prompt
    media_keyboard = [
        [InlineKeyboardButton(get_text("btn_done_media", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_DONE_MEDIA}")],
        [InlineKeyboardButton(get_text("btn_clear_media", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_CLEAR_MEDIA}")]
    ]
    return await _ask_question(update, context, "ask_media", constants.ASK_MEDIA, reply_markup_override=InlineKeyboardMarkup(media_keyboard))

async def handle_skip_generic_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: # Callback for skip description
    query = update.callback_query
    await query.answer()
    lang = get_user_lang(context)
    context.user_data['description'] = None # Mark as skipped
    logger.info(f"User {update.effective_user.id} skipped generic description.")
    # await query.edit_message_text(get_text("description_skipped", lang)) # This will be overwritten
    
    if context.user_data.pop('editing_field', None) == 'description': 
        return await show_preview(update, context, message_to_edit=query.message)

    media_keyboard = [
        [InlineKeyboardButton(get_text("btn_done_media", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_DONE_MEDIA}")],
        [InlineKeyboardButton(get_text("btn_clear_media", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_CLEAR_MEDIA}")]
    ]
    return await _ask_question(update, context, "ask_media", constants.ASK_MEDIA, reply_markup_override=InlineKeyboardMarkup(media_keyboard))

async def handle_ask_media_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: # MessageHandler for Photo/Video
    message = update.message
    lang = get_user_lang(context)
    get_common_data(update, context) # Ensures media_files list exists
    media_files = context.user_data['media_files']

    if len(media_files) >= config.MAX_MEDIA_ITEMS:
        await message.reply_text(get_text("max_media_reached", lang, max_media=config.MAX_MEDIA_ITEMS))
        return constants.ASK_MEDIA 

    file_id, media_type = (None, None)
    if message.photo: file_id, media_type = message.photo[-1].file_id, 'photo'
    elif message.video: file_id, media_type = message.video.file_id, 'video'
    
    if file_id and media_type and not any(mf['file_id'] == file_id for mf in media_files):
        media_files.append({'type': media_type, 'file_id': file_id})
        logger.info(f"User {update.effective_user.id} added {media_type}. Total: {len(media_files)}")
    
    reply_text_key = "media_received" if len(media_files) < config.MAX_MEDIA_ITEMS else "max_media_reached"
    text_to_send = get_text(reply_text_key, lang, count=len(media_files), max_media=config.MAX_MEDIA_ITEMS)
    
    keyboard_buttons = [
        [InlineKeyboardButton(get_text("btn_done_media", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_DONE_MEDIA}")]
    ]
    if media_files: # Only show clear media if there's media to clear
        keyboard_buttons.append([InlineKeyboardButton(get_text("btn_clear_media", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_CLEAR_MEDIA}")])
    
    # Reply with new status and buttons. Don't try to edit the user's media message.
    await message.reply_text(text_to_send, reply_markup=InlineKeyboardMarkup(keyboard_buttons))
    return constants.ASK_MEDIA

async def handle_done_media_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_user_lang(context)
    get_common_data(update, context) # Ensure media_files exists
    if not context.user_data.get('media_files'):
        # Send as new message because query.message might be the "Upload media..." prompt
        await context.bot.send_message(update.effective_chat.id, get_text("no_media_uploaded_error", lang))
        return constants.ASK_MEDIA
    logger.info(f"User {update.effective_user.id} finished media upload with {len(context.user_data['media_files'])} items.")
    return await show_preview(update, context, message_to_edit=query.message) # Pass message to edit

async def handle_clear_all_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_user_lang(context)
    get_common_data(update, context)
    context.user_data['media_files'] = []
    logger.info(f"User {update.effective_user.id} cleared all media.")
    
    media_keyboard = [
        [InlineKeyboardButton(get_text("btn_done_media", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_DONE_MEDIA}")]
        # No clear button again if list is empty
    ]
    # Edit the message that had the "Clear Media" button
    await query.edit_message_text(
        get_text("media_cleared", lang) + "\n\n" + get_text("ask_media", lang, max_media=config.MAX_MEDIA_ITEMS), 
        reply_markup=InlineKeyboardMarkup(media_keyboard), 
        parse_mode=ParseMode.MARKDOWN
    )
    return constants.ASK_MEDIA

# --- Preview, Edit, Post ---
async def show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, message_to_edit=None) -> int:
    get_common_data(update, context)
    lang = get_user_lang(context)
    
    # Generate the main ad content text from the formatter
    ad_content_text = message_formatter.format_preview_message(context.user_data)
    # Get the separate confirmation prompt
    confirm_prompt = get_text("preview_confirm_prompt", lang)

    keyboard = [[
        InlineKeyboardButton(get_text("btn_post", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_POST}"),
        InlineKeyboardButton(get_text("btn_edit", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_EDIT}"),
        InlineKeyboardButton(get_text("btn_cancel", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_CANCEL}"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    media_files = context.user_data.get('media_files', [])
    
    # Try to delete the previous preview/button message to avoid clutter
    if context.user_data.get('last_preview_message_id'):
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data.pop('last_preview_message_id'))
        except BadRequest:
            logger.warning("Could not delete previous preview message, it might have been deleted already.")

    sent_button_message = None
    if media_files:
        media_to_send_input = []
        for i, item in enumerate(media_files[:config.MAX_MEDIA_ITEMS]):
            caption_for_item = ad_content_text if i == 0 else None # Caption only on the first item of media group
            parse_mode_for_item = ParseMode.MARKDOWN if i == 0 else None
            if item['type'] == 'photo':
                media_to_send_input.append(InputMediaPhoto(media=item['file_id'], caption=caption_for_item, parse_mode=parse_mode_for_item))
            elif item['type'] == 'video':
                media_to_send_input.append(InputMediaVideo(media=item['file_id'], caption=caption_for_item, parse_mode=parse_mode_for_item))
        
        if media_to_send_input:
            await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media_to_send_input, read_timeout=40, write_timeout=40)
            # After media group, send the confirm prompt and buttons as a new message
            sent_button_message = await context.bot.send_message(update.effective_chat.id, text=confirm_prompt, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    if not sent_button_message: # No media, or media sending failed to produce a button message context
        # Send ad content and confirm prompt together
        full_preview_text = ad_content_text + "\n" + confirm_prompt
        # If message_to_edit was the "Done Uploading" button message, try to edit it
        if message_to_edit and message_to_edit.text != full_preview_text : # Avoid "message is not modified"
             try:
                sent_button_message = await message_to_edit.edit_text(full_preview_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
             except BadRequest: # If cannot edit (e.g. already deleted, or was a media message itself)
                sent_button_message = await context.bot.send_message(update.effective_chat.id, text=full_preview_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else: # Send as new message
            sent_button_message = await context.bot.send_message(update.effective_chat.id, text=full_preview_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    if sent_button_message:
        context.user_data['last_preview_message_id'] = sent_button_message.message_id
    
    context.user_data.pop('media_edited_flag', None) # Consume this flag
    return constants.PREVIEW

async def handle_preview_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data.split(constants.ACTION_CALLBACK_PREFIX)[1]
    lang = get_user_lang(context)
    get_common_data(update, context) # Ensure all user_data parts are initialized

    if action == constants.ACTION_POST:
        final_post_ad_text = message_formatter.format_final_post(context.user_data)
        media_files = context.user_data.get('media_files', [])
        
        # Save to DB first
        post_id = await db.save_post(context.user_data)
        logger.info(f"Post {post_id} data saved for user {update.effective_user.id}, proceeding to publish.")

        target_chat = config.TARGET_CHAT_ID
        sent_channel_message = None
        try:
            if media_files:
                media_to_send_channel = []
                for i, item in enumerate(media_files[:config.MAX_MEDIA_ITEMS]):
                    caption_for_item = final_post_ad_text if i == 0 else None
                    parse_mode_for_item = ParseMode.MARKDOWN if i == 0 else None
                    if item['type'] == 'photo':
                        media_to_send_channel.append(InputMediaPhoto(media=item['file_id'], caption=caption_for_item, parse_mode=parse_mode_for_item))
                    elif item['type'] == 'video':
                        media_to_send_channel.append(InputMediaVideo(media=item['file_id'], caption=caption_for_item, parse_mode=parse_mode_for_item))
                
                if media_to_send_channel:
                    sent_channel_messages_list = await context.bot.send_media_group(chat_id=target_chat, media=media_to_send_channel, read_timeout=60, write_timeout=60)
                    sent_channel_message = sent_channel_messages_list[0] if sent_channel_messages_list else None
            
            if not sent_channel_message: # No media, or media_group sending failed, send as text
                # If media_files existed but media_to_send_channel was empty or send_media_group failed,
                # this will send the text part.
                sent_channel_message = await context.bot.send_message(
                    chat_id=target_chat, text=final_post_ad_text, parse_mode=ParseMode.MARKDOWN
                )
            
            if sent_channel_message:
                await db.update_post_status(post_id, 'published', sent_channel_message.message_id)
                success_msg_key = "post_successful_channel" if config.IS_CHANNEL else "post_successful_admin"
                await query.edit_message_text(get_text(success_msg_key, lang, target_chat_id=str(target_chat)))
            else:
                await db.update_post_status(post_id, 'failed_to_publish_no_message_sent')
                logger.error(f"Post {post_id} to {target_chat} resulted in no sent_channel_message.")
                await query.edit_message_text(get_text("general_error", lang) + "\n(Post could not be sent to channel/admin)")

        except Exception as e:
            logger.error(f"Error posting to target {target_chat} for post {post_id}: {e}", exc_info=True)
            await db.update_post_status(post_id, 'failed_to_publish_exception')
            await query.edit_message_text(get_text("general_error", lang) + f"\nDebug Info: {str(e)[:100]}")
        
        await clear_user_data_for_new_post(context)
        return ConversationHandler.END

    elif action == constants.ACTION_EDIT:
        logger.info(f"User {update.effective_user.id} chose to edit post.")
        return await ask_edit_choice(update, context)

    elif action == constants.ACTION_CANCEL:
        logger.info(f"User {update.effective_user.id} cancelled post creation.")
        await query.edit_message_text(get_text("post_cancelled", lang))
        await clear_user_data_for_new_post(context)
        return ConversationHandler.END
    
    return constants.PREVIEW


async def ask_edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query # Edit is always initiated by a callback
    lang = get_user_lang(context)
    get_common_data(update, context)
    category = context.user_data.get('category')
    specific_data = context.user_data.get(constants.CAT_SPECIFIC_DATA_KEY, {})

    buttons = []
    # Add common fields first
    for field_key, state_const in constants.EDITABLE_FIELDS_COMMON.items():
        # Check if the field has data or is applicable
        if field_key in context.user_data or (field_key == 'description' and context.user_data.get(field_key) is not None):
             buttons.append(InlineKeyboardButton(
                get_text(f"btn_edit_{field_key}", lang), # e.g. btn_edit_price
                callback_data=f"{constants.EDIT_FIELD_CALLBACK_PREFIX}{field_key}"
            ))

    # Add category-specific fields
    if category and category in constants.EDITABLE_FIELDS_CATEGORY:
        for field_key, state_const in constants.EDITABLE_FIELDS_CATEGORY[category].items():
            if field_key in specific_data and specific_data[field_key] is not None : # Only show if data exists
                # Need localization keys like "btn_edit_car_make_model"
                loc_key = f"btn_edit_{field_key}"
                button_text = get_text(loc_key, lang)
                if f"_{loc_key}_" in button_text: # Fallback if specific loc key not found
                    button_text = field_key.replace("_", " ").title() 
                buttons.append(InlineKeyboardButton(
                    button_text,
                    callback_data=f"{constants.EDIT_FIELD_CALLBACK_PREFIX}{field_key}"
                ))
    
    if not buttons: # No editable fields found (should not happen if price/location were asked)
        await query.answer("No editable fields available for this ad yet.", show_alert=True)
        return await show_preview(update, context, message_to_edit=query.message)


    keyboard_rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)] # 2 buttons per row
    keyboard_rows.append([
        InlineKeyboardButton(get_text("btn_back_to_preview", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_BACK_TO_PREVIEW}")
    ])
    reply_markup = InlineKeyboardMarkup(keyboard_rows)

    await query.edit_message_text(get_text("edit_choice_prompt", lang), reply_markup=reply_markup)
    return constants.EDIT_CHOICE


# In handlers/conversation_flow.py
async def handle_edit_field_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_key_to_edit = query.data.split(constants.EDIT_FIELD_CALLBACK_PREFIX)[1]
    lang = get_user_lang(context)
    category = context.user_data.get('category')

    # Flag to return to preview after the field is re-entered
    context.user_data['editing_field'] = selected_key_to_edit 
    # For category-specific, we might need a more unique editing_field flag
    # e.g., context.user_data['editing_field'] = f"{category}_{selected_key_to_edit}"
    # and then the respective _handle_text_input needs to check this modified flag.
    # Let's keep it simple for now and see if it works, if not, we adjust the flag.

    # Common fields
    if selected_key_to_edit == "price":
        return await _ask_question(update, context, "ask_price", constants.ASK_PRICE)
    if selected_key_to_edit == "location":
        return await _ask_question(update, context, "ask_location", constants.ASK_LOCATION)
    if selected_key_to_edit == "description":
        # For description, _ask_question already adds the skip button if question_key is "ask_description"
        return await _ask_question(update, context, "ask_description", constants.ASK_DESCRIPTION)
    if selected_key_to_edit == "media":
        context.user_data['media_edited_flag'] = True 
        context.user_data['media_files'] = [] 
        logger.info("Media cleared for re-upload during edit.")
        media_keyboard = [[InlineKeyboardButton(get_text("btn_done_media", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_DONE_MEDIA}")],
                          [InlineKeyboardButton(get_text("btn_clear_media", lang), callback_data=f"{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_CLEAR_MEDIA}")]]
        return await _ask_question(update, context, "ask_media", constants.ASK_MEDIA, reply_markup_override=InlineKeyboardMarkup(media_keyboard))

    # Category-specific fields
    if category and category in constants.EDITABLE_FIELDS_CATEGORY:
        cat_fields = constants.EDITABLE_FIELDS_CATEGORY[category]
        if selected_key_to_edit in cat_fields:
            target_state_for_reask = cat_fields[selected_key_to_edit] # e.g., constants.CAR_MAKE_MODEL
            question_key_loc = f"ask_{selected_key_to_edit}" # e.g., "ask_car_make_model"
            
            logger.info(f"Editing category-specific field: {selected_key_to_edit}. Target state: {target_state_for_reask}. Question key: {question_key_loc}")

            # Determine if the original question for this field was optional and needs a skip button
            is_optional_edit = False
            optional_field_key_edit = None
            # Example: For 'car_year', its original ask had 'is_optional=True'
            if selected_key_to_edit == "car_year" or \
               selected_key_to_edit == "house_rooms" or \
               selected_key_to_edit == "house_area" or \
               selected_key_to_edit == "house_year_built" or \
               selected_key_to_edit == "animal_breed" or \
               selected_key_to_edit == "animal_sex":
                is_optional_edit = True
                optional_field_key_edit = selected_key_to_edit # e.g. "car_year"

            # Special handling for fields that require inline choice buttons
            if selected_key_to_edit == 'house_property_type':
                prop_types = ["apartment", "house", "land", "commercial", "other"]
                keyboard_prop = [] 
                row = []
                for pt_key in prop_types:
                    row.append(InlineKeyboardButton(get_text(f"property_type_{pt_key}", lang), callback_data=f"{constants.PROPERTY_TYPE_CALLBACK_PREFIX}{pt_key}"))
                    if len(row) == 2: keyboard_prop.append(row); row = []
                if row: keyboard_prop.append(row)
                return await _ask_question(update, context, question_key_loc, target_state_for_reask, reply_markup_override=InlineKeyboardMarkup(keyboard_prop))
            
            if selected_key_to_edit == 'animal_sex':
                sex_keyboard_buttons = [
                    [InlineKeyboardButton(get_text("animal_sex_male", lang), callback_data=f"{constants.ANIMAL_SEX_CALLBACK_PREFIX}male"),
                     InlineKeyboardButton(get_text("animal_sex_female", lang), callback_data=f"{constants.ANIMAL_SEX_CALLBACK_PREFIX}female")],
                    [InlineKeyboardButton(get_text("btn_skip", lang), callback_data=f"{constants.SKIP_FIELD_CALLBACK_PREFIX}animal_sex")]
                ]
                return await _ask_question(update, context, question_key_loc, target_state_for_reask, reply_markup_override=InlineKeyboardMarkup(sex_keyboard_buttons))

            # For regular text input fields
            return await _ask_question(update, context, question_key_loc, target_state_for_reask, 
                                       is_optional=is_optional_edit, optional_field_key=optional_field_key_edit)

    # Fallback if field not explicitly handled for edit
    logger.warning(f"Edit attempt for unhandled field key: {selected_key_to_edit} in category {category}")
    await query.message.reply_text(get_text("general_error", lang) + " (Edit for this field not fully set up).", parse_mode=ParseMode.MARKDOWN)
    return constants.EDIT_CHOICE # Stay in edit choice to allow user to pick another or go back

async def handle_back_to_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # query = update.callback_query; await query.answer() # Answered by show_preview if it edits
    return await show_preview(update, context, message_to_edit=update.callback_query.message)

async def unknown_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(context)
    logger.warning(f"User {update.effective_user.id} sent unexpected text '{update.message.text}' when specific input or button was expected.")
    await update.message.reply_text(get_text("invalid_input", lang))
    # No state change, user remains in the current state.

# --- Conversation Handler Definitions ---
def create_ad_posting_conversation_handler() -> ConversationHandler:
    # (States dictionary definition is exactly as in the previous large handler code block)
    # This is long, so I'll skip re-pasting the full 'states' dict here.
    # Ensure all state constants map to their respective handler functions.
    states = {
        constants.LANG_SELECT: [CallbackQueryHandler(handle_language_selection, pattern=f"^{constants.LANG_CALLBACK_PREFIX}(?!change_)")],
        constants.CATEGORY_SELECT: [CallbackQueryHandler(handle_category_selection, pattern=f"^{constants.CATEGORY_CALLBACK_PREFIX}")],
        
        constants.CAR_MAKE_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_car_make_model)],
        constants.CAR_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_car_year), CallbackQueryHandler(skip_car_year, pattern=f"^{constants.SKIP_FIELD_CALLBACK_PREFIX}car_year$")],
        constants.CAR_MILEAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_car_mileage)],

        constants.HOUSE_PROPERTY_TYPE: [CallbackQueryHandler(handle_house_property_type, pattern=f"^{constants.PROPERTY_TYPE_CALLBACK_PREFIX}")],
        constants.HOUSE_ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_house_rooms), CallbackQueryHandler(skip_house_rooms, pattern=f"^{constants.SKIP_FIELD_CALLBACK_PREFIX}house_rooms$")],
        constants.HOUSE_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_house_area), CallbackQueryHandler(skip_house_area, pattern=f"^{constants.SKIP_FIELD_CALLBACK_PREFIX}house_area$")],
        constants.HOUSE_YEAR_BUILT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_house_year_built), CallbackQueryHandler(skip_house_year_built, pattern=f"^{constants.SKIP_FIELD_CALLBACK_PREFIX}house_year_built$")],

        constants.ANIMAL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_animal_type)],
        constants.ANIMAL_BREED: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_animal_breed), CallbackQueryHandler(skip_animal_breed, pattern=f"^{constants.SKIP_FIELD_CALLBACK_PREFIX}animal_breed$")],
        constants.ANIMAL_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_animal_age)], # This will internally ask for sex
        constants.ANIMAL_SEX: [CallbackQueryHandler(handle_animal_sex, pattern=f"^{constants.ANIMAL_SEX_CALLBACK_PREFIX}"), CallbackQueryHandler(skip_animal_sex, pattern=f"^{constants.SKIP_FIELD_CALLBACK_PREFIX}animal_sex$")],
        
        constants.OTHER_ITEM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_other_item_name)],

        constants.ASK_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ask_price)],
        constants.ASK_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ask_location)],
        constants.ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ask_description), CallbackQueryHandler(handle_skip_generic_description, pattern=f"^{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_SKIP_DESCRIPTION}$")],
        constants.ASK_MEDIA: [
            MessageHandler(filters.PHOTO | filters.VIDEO & ~filters.COMMAND, handle_ask_media_files), 
            CallbackQueryHandler(handle_done_media_upload, pattern=f"^{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_DONE_MEDIA}$"),
            CallbackQueryHandler(handle_clear_all_media, pattern=f"^{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_CLEAR_MEDIA}$")
        ],
        constants.PREVIEW: [CallbackQueryHandler(handle_preview_action, pattern=f"^{constants.ACTION_CALLBACK_PREFIX}({constants.ACTION_POST}|{constants.ACTION_EDIT}|{constants.ACTION_CANCEL})$")],
        constants.EDIT_CHOICE: [
            CallbackQueryHandler(handle_edit_field_selection, pattern=f"^{constants.EDIT_FIELD_CALLBACK_PREFIX}"),
            CallbackQueryHandler(handle_back_to_preview, pattern=f"^{constants.ACTION_CALLBACK_PREFIX}{constants.ACTION_BACK_TO_PREVIEW}$")
        ],
        ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, timeout_conversation)]
    }
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states=states,
        fallbacks=[
            CommandHandler('cancel', cancel_conversation),
            MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text_input)
        ],
        conversation_timeout=config.CONVERSATION_TIMEOUT_DURATION,
        per_user=True, 
        per_chat=True,
        # NEW PARAMETER:
        allow_reentry=True  # <--- ADD THIS!
    )
    return conv_handler

def create_language_change_conversation_handler() -> ConversationHandler:
    lang_change_conv = ConversationHandler(
        entry_points=[CommandHandler('language', language_command)],
        states={
            constants.CHANGE_LANG_PROMPT: [
                CallbackQueryHandler(handle_language_change_selection, pattern=f"^{constants.LANG_CALLBACK_PREFIX}change_")
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)], # Generic cancel can end this too
        conversation_timeout=60 * 5, # 5 minutes
        per_user=True, per_chat=True,
        # name="language_change_conversation",
    )
    return lang_change_conv