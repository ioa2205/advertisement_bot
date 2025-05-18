# selling_bot/services/message_formatter.py
from typing import Dict, Any
from localization import get_text, get_user_lang, get_category_display_name
from config import CATEGORIES_KEYS, DEFAULT_LANGUAGE # Import CATEGORIES_KEYS
from constants import CAT_SPECIFIC_DATA_KEY # Import the key

def format_preview_message(user_data: Dict[str, Any]) -> str:
    """Formats the ad preview message based on category."""
    lang = user_data.get('lang', DEFAULT_LANGUAGE)
    category_key = user_data.get('category', CATEGORIES_KEYS["other"]) # Default to 'other' if not set
    
    specific_data = user_data.get(CAT_SPECIFIC_DATA_KEY, {})

    # Get the localized display name for the category
    category_display = get_category_display_name(category_key, lang)
    
    # Get the localized title format for the category
    # e.g., "preview_title_cars", "preview_title_houses"
    title_text_key = f"preview_title_{category_key}"
    # Fallback to a generic title if specific one isn't found (though it should be)
    title_text = get_text(title_text_key, lang, category_display_name=category_display)
    if f"_{title_text_key}_" in title_text: # Check if key wasn't found in localization
        title_text = get_text("preview_title_other", lang, category_display_name=category_display) # Fallback

    parts = [title_text]

    # --- Category-Specific Fields ---
    if category_key == CATEGORIES_KEYS["cars"]:
        if specific_data.get('car_make_model'):
            parts.append(get_text("preview_field_car_make_model", lang, value=specific_data['car_make_model']))
        if specific_data.get('car_year'):
            parts.append(get_text("preview_field_car_year", lang, value=specific_data['car_year']))
        if specific_data.get('car_mileage'):
            parts.append(get_text("preview_field_car_mileage", lang, value=specific_data['car_mileage']))

    elif category_key == CATEGORIES_KEYS["houses"]:
        if specific_data.get('house_property_type'):
            parts.append(get_text("preview_field_house_property_type", lang, value=specific_data['house_property_type']))
        if specific_data.get('house_rooms'):
            parts.append(get_text("preview_field_house_rooms", lang, value=specific_data['house_rooms']))
        if specific_data.get('house_area'):
            parts.append(get_text("preview_field_house_area", lang, value=specific_data['house_area']))
        if specific_data.get('house_year_built'):
            parts.append(get_text("preview_field_house_year_built", lang, value=specific_data['house_year_built']))

    elif category_key == CATEGORIES_KEYS["animals"]:
        if specific_data.get('animal_type'):
            parts.append(get_text("preview_field_animal_type", lang, value=specific_data['animal_type']))
        if specific_data.get('animal_breed'):
            parts.append(get_text("preview_field_animal_breed", lang, value=specific_data['animal_breed']))
        if specific_data.get('animal_age'):
            parts.append(get_text("preview_field_animal_age", lang, value=specific_data['animal_age']))
        if specific_data.get('animal_sex'):
            parts.append(get_text("preview_field_animal_sex", lang, value=specific_data['animal_sex']))

    elif category_key == CATEGORIES_KEYS["other"]:
        if specific_data.get('other_item_name'): # Assuming 'title' was the generic one
            parts.append(get_text("preview_field_other_item_name", lang, value=specific_data.get('other_item_name')))
        # If you had a generic 'title' for 'other' items before, you might use user_data.get('title')

    # --- Common Fields ---
    if user_data.get('price'):
        parts.append(get_text("preview_field_price", lang, value=user_data['price']))
    if user_data.get('location'):
        parts.append(get_text("preview_field_location", lang, value=user_data['location']))
    
    description = user_data.get('description')
    if description:
        parts.append(get_text("preview_field_description", lang, value=description))
    else:
        # Only add "No description" if it's not an "other" item that might have its own "item name" as the primary text
        # Or always show it if no specific content fields were filled.
        # For simplicity, let's show it if the description field itself is empty.
        parts.append(get_text("preview_field_no_description", lang))

    # --- Media Info ---
    media_files = user_data.get('media_files', [])
    if media_files:
        photo_count = sum(1 for item in media_files if item['type'] == 'photo')
        video_count = sum(1 for item in media_files if item['type'] == 'video')
        if photo_count > 0 and video_count == 0:
            parts.append(get_text("preview_media_info_photo", lang, count=photo_count))
        elif video_count > 0 and photo_count == 0:
            parts.append(get_text("preview_media_info_video", lang, count=video_count))
        elif photo_count > 0 and video_count > 0: # Check if both > 0
             parts.append(get_text("preview_media_info_mixed", lang, count=len(media_files)))
        # elif len(media_files) > 0: # General fallback if only one type but previous conditions missed
        #     parts.append(get_text("preview_media_info_mixed", lang, count=len(media_files)))


    return "\n".join(parts)

def format_final_post(user_data: Dict[str, Any]) -> str:
    """Formats the final post message (currently uses the same logic as preview)."""
    # For the channel post, you might want a slightly different or more compact format.
    # But for now, reusing the preview format is fine.
    return format_preview_message(user_data)