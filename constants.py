# constants.py

# Main Conversation states

(
    # Core Flow & Utilities
    LANG_SELECT,                # 0
    CATEGORY_SELECT,            # 1
    PREVIEW,                    # 2
    EDIT_CHOICE,                # 3
    CHANGE_LANG_PROMPT,         # 4

    # Common Input Steps (can be targets from category flows)
    ASK_PRICE,                  # 5
    ASK_LOCATION,               # 6
    ASK_DESCRIPTION,            # 7
    ASK_MEDIA,                  # 8

    # Category: Cars
    CAR_MAKE_MODEL,             # 9
    CAR_YEAR,                   # 10 (Optional)
    CAR_MILEAGE,                # 11

    # Category: Houses
    HOUSE_PROPERTY_TYPE,        # 12
    HOUSE_ROOMS,                # 13 (Optional)
    HOUSE_AREA,                 # 14 (Optional)
    HOUSE_YEAR_BUILT,           # 15 (Optional)

    # Category: Animals
    ANIMAL_TYPE,                # 16
    ANIMAL_BREED,               # 17 (Optional)
    ANIMAL_AGE,                 # 18
    ANIMAL_SEX,                 # 19 (Optional)

    # Category: Other
    OTHER_ITEM_NAME,            # 20
) = range(21) 


# Callback data prefixes
LANG_CALLBACK_PREFIX = "lang_"
CATEGORY_CALLBACK_PREFIX = "cat_"
ACTION_CALLBACK_PREFIX = "action_"
EDIT_FIELD_CALLBACK_PREFIX = "edit_field_"
SKIP_FIELD_CALLBACK_PREFIX = "skip_field_" # For optional fields
PROPERTY_TYPE_CALLBACK_PREFIX = "prop_type_"
ANIMAL_SEX_CALLBACK_PREFIX = "animal_sex_"


# Callback data values for specific actions
ACTION_POST = "post"
ACTION_EDIT = "edit"
ACTION_CANCEL = "cancel"
ACTION_DONE_MEDIA = "done_media"
ACTION_CLEAR_MEDIA = "clear_media"
ACTION_SKIP_DESCRIPTION = "skip_description" # Keep for generic description
ACTION_BACK_TO_PREVIEW = "back_to_preview"


# Fields that can be edited
EDITABLE_FIELDS_COMMON = {  # <--- RENAMED FROM EDITABLE_FIELDS
    "price": ASK_PRICE,
    "location": ASK_LOCATION,
    "description": ASK_DESCRIPTION,
    "media": ASK_MEDIA,
}

# You can keep this for future reference or if you decide to build the dynamic category edit menu
EDITABLE_FIELDS_CATEGORY = {
    "cars": {
        "car_make_model": CAR_MAKE_MODEL,
        "car_year": CAR_YEAR,
        "car_mileage": CAR_MILEAGE,
    },
    "houses": {
        "house_property_type": HOUSE_PROPERTY_TYPE,
        "house_rooms": HOUSE_ROOMS, # Assuming you have state constants for these
        "house_area": HOUSE_AREA,
        "house_year_built": HOUSE_YEAR_BUILT,
    },
    "animals": {
        "animal_type": ANIMAL_TYPE,
        "animal_breed": ANIMAL_BREED,
        "animal_age": ANIMAL_AGE,
        "animal_sex": ANIMAL_SEX,
    },
    "other": {
        "other_item_name": OTHER_ITEM_NAME,
    }
}
# Key for storing category-specific data dict within user_data
CAT_SPECIFIC_DATA_KEY = "category_specific_data"