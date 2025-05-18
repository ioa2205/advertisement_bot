# selling_bot/localization.py
from telegram.ext import ContextTypes
from config import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, MAX_MEDIA_ITEMS, CATEGORIES_KEYS # MAX_DESCRIPTION_LENGTH removed temporarily from here, handled in get_text
# from config import MAX_DESCRIPTION_LENGTH # Import directly in get_text if needed

strings = {
    'en': {
        # --- General & Existing ---
        "welcome": "Hi {name}! Please choose your language:",
        "lang_chosen": "Language set to English.",
        "choose_category": "What do you want to sell?",
        # Category chosen will be followed by the first specific question for that category
        "ask_price": "What's the *asking price*? (e.g., $15,000 or 15000 USD)", # Generic price prompt
        "ask_location": "In which *city or district* is the item located?", # Generic location prompt
        "ask_description": "Add a *brief description* (optional, max {max_desc_len} chars).\nSend your description or use the button below to skip.",
        "ask_media": "Upload photos or videos (up to {max_media} files).\nSend your media, then use the buttons below.",
        "media_received": "Media received ({count}/{max_media}). Send more or press 'Done'.",
        "max_media_reached": "Maximum number of media files ({max_media}) reached. Press 'Done'.",
        "no_media_uploaded_error": "Please upload at least one photo or video.",
        "preview_confirm_prompt": "\n— — — — —\n\n✅ Confirm to publish?\nChoose an option:",
        "btn_post": "✅ Post", "btn_edit": "✏️ Edit", "btn_cancel": "❌ Cancel",
        "post_successful_channel": "✅ Successfully posted to {target_chat_id}!",
        "post_successful_admin": "✅ Your ad has been submitted for review!",
        "post_cancelled": "Publication cancelled. You can start over with /start.",
        "edit_choice_prompt": "What would you like to edit? (Note: Some fields may require restarting that section)", # Updated edit prompt
        "btn_edit_price": "💰 Price", "btn_edit_location": "🗺️ Location", "btn_edit_description": "📄 Description", "btn_edit_media": "🖼️ Media",
        "btn_back_to_preview": "↩️ Back to Preview", "btn_done_media": "✅ Done Uploading", "btn_clear_media": "🔄 Clear All Media",
        "btn_skip": "➡️ Skip", # Generic Skip button
        "btn_skip_description": "➡️ Skip Description", # Can be merged with btn_skip if context is clear
        "description_skipped": "Description skipped.", "media_cleared": "All media cleared. You can now upload new ones.",
        "invalid_input": "Sorry, I didn't understand that. Please follow the instructions or use the buttons provided.",
        "price_invalid": "Invalid price format. Please enter a valid price (e.g., 15000, $15000, 150.00 EUR).",
        "description_too_long": "Description is too long (max {max_desc_len} characters). Please shorten it.",
        "general_error": "An error occurred. Please try again or type /cancel to restart.",
        "timeout_message": "Conversation timed out due to inactivity. Please start over with /start.",
        "conversation_restarted": "The previous operation was cancelled. Let's start over.",
        "category_cars": "🚗 Cars", "category_houses": "🏠 Real Estate", "category_animals": "🐄 Animals", "category_other": "🧸 Other",
        "change_language_prompt": "Please choose your new language:",
        "language_changed_success": "Language successfully changed to {new_lang_display}. Your current ad creation process has been reset. Please use /start to begin a new ad.",
        "help_message": (
            "Welcome to the Ad Posting Bot!\n\n"
            "Here's how to create an ad:\n"
            "1. Use /start to begin.\n"
            "2. Select a category and follow the prompts for details.\n"
            "3. Upload photos/videos when asked.\n"
            "4. Review your ad and then post, edit, or cancel.\n\n"
            "Available commands:\n"
            "/start - Create a new ad.\n"
            "/language - Change your preferred language.\n"
            "/help - Show this help message.\n"
            "/cancel - Cancel the current ad creation process."
        ),
        "field_skipped": "{field_name} skipped.", # Generic skip message

        # --- Category: Cars ---
        "category_chosen_cars": "🚗 Great! Let's get details for the car.",
        "ask_car_make_model": "What's the *Make and Model* of the car (e.g., Toyota Camry, BMW X5)?",
        "ask_car_year": "What's the car's *Year of Manufacture* (e.g., 2018)? (Optional)",
        "ask_car_mileage": "What's the car's *Mileage* (e.g., 55000 km or 30000 miles)?",
        "preview_title_cars": "📢 **Car for Sale**",
        "preview_field_car_make_model": "**Make/Model:** {value}",
        "preview_field_car_year": "**Year:** {value}",
        "preview_field_car_mileage": "🛣️ **Mileage:** {value}",
        "btn_edit_car_make_model": "Make/Model",
        "btn_edit_car_year": "Year",
        "btn_edit_car_mileage": "Mileage",

        # --- Category: Houses/Real Estate ---
        "category_chosen_houses": "🏠 Okay! Let's get details for the property.",
        "ask_house_property_type": "What *type of property* is it?",
        "ask_house_rooms": "How many *rooms* does it have (e.g., 3)? (Optional)",
        "ask_house_area": "What's the approximate *area or size* (e.g., 75 sqm, 1200 sqft)? (Optional)",
        "ask_house_year_built": "In what *year was it built* (e.g., 2010)? (Optional)",
        "property_type_apartment": "Apartment", "property_type_house": "House", "property_type_land": "Land", "property_type_commercial": "Commercial Space", "property_type_other": "Other Type",
        "preview_title_houses": "📢 **Property for Sale**",
        "preview_field_house_property_type": "**Type:** {value}",
        "preview_field_house_rooms": "**Rooms:** {value}",
        "preview_field_house_area": "📐 **Area:** {value}",
        "preview_field_house_year_built": "**Year Built:** {value}",
        "btn_edit_house_property_type": "Property Type", 
        "btn_edit_house_rooms": "Rooms", 
        "btn_edit_house_area": "Area", 
        "btn_edit_house_year_built": "Year Built",

        # --- Category: Animals ---
        "category_chosen_animals": "🐄 Got it! Let's get details for the animal.",
        "ask_animal_type": "What *type of animal* is it (e.g., Dog, Cat, Cow)?",
        "ask_animal_breed": "What's the *breed* of the {animal_type_placeholder}? (Optional)",
        "ask_animal_age": "How *old* is the animal (e.g., 2 years, 6 months)?",
        "ask_animal_sex": "What is the animal's *sex*? (Optional)",
        "animal_sex_male": "Male", "animal_sex_female": "Female",
        "preview_title_animals": "📢 **Animal for Sale/Adoption**",
        "preview_field_animal_type": "**Animal Type:** {value}",
        "preview_field_animal_breed": "**Breed:** {value}",
        "preview_field_animal_age": "**Age:** {value}",
        "preview_field_animal_sex": "**Sex:** {value}",
        "btn_edit_animal_type": "Animal Type", 
        "btn_edit_animal_breed": "Breed", 
        "btn_edit_animal_age": "Age", 
        "btn_edit_animal_sex": "Sex",

        # --- Category: Other ---
        "category_chosen_other": "🧸 Understood! Let's get details for your item.",
        "ask_other_item_name": "What is the *name or type* of item you're selling?",
        "preview_title_other": "📢 **Item for Sale**",
        "preview_field_other_item_name": "**Item:** {value}",
        "btn_edit_other_item_name": "Item Name",

        # --- Common Preview Fields (can be used by all categories) ---
        "preview_field_price": "💵 **Price:** {value}",
        "preview_field_location": "📍 **Location:** {value}",
        "preview_field_description": "📝 **Description:** {value}",
        "preview_field_no_description": "📝 **Description:** (No description provided)",
        "preview_media_info_photo": "📸 {count} Photo(s)",
        "preview_media_info_video": "📹 {count} Video(s)",
        "preview_media_info_mixed": "🖼️ {count} Media file(s)",
    },
    'ru': {
        # --- General & Existing ---
        "welcome": "Привет, {name}! Пожалуйста, выберите язык:",
        "lang_chosen": "Язык установлен на Русский.",
        "choose_category": "Что вы хотите продать?",
        "ask_price": "Какая *цена*? (например, 1000000 руб. или $15000)",
        "ask_location": "В каком *городе или районе* находится товар?",
        "ask_description": "Добавьте *краткое описание* (необязательно, макс. {max_desc_len} симв.).\nОтправьте описание или используйте кнопку ниже, чтобы пропустить.",
        "ask_media": "Загрузите фото или видео (до {max_media} файлов).\nОтправьте медиафайлы, затем используйте кнопки ниже.",
        "media_received": "Медиафайл получен ({count}/{max_media}). Отправьте еще или нажмите 'Готово'.",
        "max_media_reached": "Достигнуто максимальное количество медиафайлов ({max_media}). Нажмите 'Готово'.",
        "no_media_uploaded_error": "Пожалуйста, загрузите хотя бы одно фото или видео.",
        "preview_confirm_prompt": "\n— — — — —\n\n✅ Подтвердить публикацию?\nВыберите действие:",
        "btn_post": "✅ Опубликовать", "btn_edit": "✏️ Редактировать", "btn_cancel": "❌ Отменить",
        "post_successful_channel": "✅ Успешно опубликовано в {target_chat_id}!",
        "post_successful_admin": "✅ Ваше объявление отправлено на рассмотрение!",
        "post_cancelled": "Публикация отменена. Вы можете начать заново с /start.",
        "edit_choice_prompt": "Что бы вы хотели отредактировать? (Примечание: некоторые поля могут потребовать перезапуска этого раздела)",
        "btn_edit_price": "💰 Цена", "btn_edit_location": "🗺️ Местоположение", "btn_edit_description": "📄 Описание", "btn_edit_media": "🖼️ Медиа",
        "btn_back_to_preview": "↩️ Назад к предпросмотру", "btn_done_media": "✅ Готово с медиа", "btn_clear_media": "🔄 Очистить медиа",
        "btn_skip": "➡️ Пропустить",
        "btn_skip_description": "➡️ Пропустить описание",
        "description_skipped": "Описание пропущено.", "media_cleared": "Все медиафайлы удалены. Можете загрузить новые.",
        "invalid_input": "Извините, я не понял. Пожалуйста, следуйте инструкциям или используйте кнопки.",
        "price_invalid": "Неверный формат цены. Пожалуйста, введите корректную цену (например, 15000, $15000, 150.00 EUR).",
        "description_too_long": "Описание слишком длинное (макс. {max_desc_len} символов). Пожалуйста, сократите его.",
        "general_error": "Произошла ошибка. Пожалуйста, попробуйте еще раз или напишите /cancel для перезапуска.",
        "timeout_message": "Время сессии истекло из-за неактивности. Пожалуйста, начните заново с /start.",
        "conversation_restarted": "Предыдущая операция была отменена. Давайте начнем сначала.",
        "category_cars": "🚗 Автомобили", "category_houses": "🏠 Недвижимость", "category_animals": "🐄 Животные", "category_other": "🧸 Другое",
        "change_language_prompt": "Пожалуйста, выберите новый язык:",
        "language_changed_success": "Язык успешно изменен на {new_lang_display}. Текущий процесс создания объявления сброшен. Используйте /start, чтобы начать новое объявление.",
        "help_message": (
            "Добро пожаловать в бот для публикации объявлений!\n\n"
            "Как создать объявление:\n"
            "1. Используйте /start, чтобы начать.\n"
            "2. Выберите категорию и следуйте инструкциям для указания деталей.\n"
            "3. Загрузите фото/видео по запросу.\n"
            "4. Просмотрите объявление, затем опубликуйте, отредактируйте или отмените.\n\n"
            "Доступные команды:\n"
            "/start - Создать новое объявление.\n"
            "/language - Изменить предпочитаемый язык.\n"
            "/help - Показать это справочное сообщение.\n"
            "/cancel - Отменить текущий процесс создания объявления."
        ),
        "field_skipped": "{field_name} пропущено.",

        # --- Category: Cars ---
        "category_chosen_cars": "🚗 Отлично! Давайте уточним детали автомобиля.",
        "ask_car_make_model": "Укажите *Марку и Модель* автомобиля (например, Toyota Camry, BMW X5)?",
        "ask_car_year": "Какой *Год выпуска* автомобиля (например, 2018)? (Необязательно)",
        "ask_car_mileage": "Какой *Пробег* у автомобиля (например, 55000 км)?",
        "preview_title_cars": "📢 **Продается Автомобиль**",
        "preview_field_car_make_model": "**Марка/Модель:** {value}",
        "preview_field_car_year": "**Год:** {value}",
        "preview_field_car_mileage": "🛣️ **Пробег:** {value}",
        "btn_edit_car_make_model": "Марка/Модель", # NEW RUSSIAN
        "btn_edit_car_year": "Год",               # NEW RUSSIAN
        "btn_edit_car_mileage": "Пробег", 

        # --- Category: Houses/Real Estate ---
        "category_chosen_houses": "🏠 Хорошо! Давайте уточним детали недвижимости.",
        "ask_house_property_type": "Какой *тип недвижимости* вы продаете?",
        "ask_house_rooms": "Сколько *комнат* (например, 3)? (Необязательно)",
        "ask_house_area": "Какая примерная *площадь* (например, 75 кв.м, 12 соток)? (Необязательно)",
        "ask_house_year_built": "В каком *году построен* (например, 2010)? (Необязательно)",
        "property_type_apartment": "Квартира", "property_type_house": "Дом", "property_type_land": "Земельный участок", "property_type_commercial": "Коммерческое помещение", "property_type_other": "Другой тип",
        "preview_title_houses": "📢 **Продается Недвижимость**",
        "preview_field_house_property_type": "**Тип:** {value}",
        "preview_field_house_rooms": "**Комнат:** {value}",
        "preview_field_house_area": "📐 **Площадь:** {value}",
        "preview_field_house_year_built": "**Год постройки:** {value}",
        "btn_edit_house_property_type": "Тип недвижимости", # NEW RUSSIAN
        "btn_edit_house_rooms": "Комнаты",                 # NEW RUSSIAN
        "btn_edit_house_area": "Площадь",                 # NEW RUSSIAN
        "btn_edit_house_year_built": "Год постройки",   

        # --- Category: Animals ---
        "category_chosen_animals": "🐄 Понятно! Давайте уточним детали о животном.",
        "ask_animal_type": "Какое *животное* вы продаете (например, Собака, Кошка, Корова)?",
        "ask_animal_breed": "Какая *порода* у {animal_type_placeholder}? (Необязательно)",
        "ask_animal_age": "Какой *возраст* у животного (например, 2 года, 6 месяцев)?",
        "ask_animal_sex": "Какой *пол* у животного? (Необязательно)",
        "animal_sex_male": "Самец", "animal_sex_female": "Самка",
        "preview_title_animals": "📢 **Продается/Отдается Животное**",
        "preview_field_animal_type": "**Вид животного:** {value}",
        "preview_field_animal_breed": "**Порода:** {value}",
        "preview_field_animal_age": "**Возраст:** {value}",
        "preview_field_animal_sex": "**Пол:** {value}",
        "btn_edit_animal_type": "Вид животного",     # NEW RUSSIAN
        "btn_edit_animal_breed": "Порода",           # NEW RUSSIAN
        "btn_edit_animal_age": "Возраст",           # NEW RUSSIAN
        "btn_edit_animal_sex": "Пол",               # NEW RUSSIAN

        # --- Category: Other ---
        "category_chosen_other": "🧸 Ясно! Давайте уточним детали вашего товара.",
        "ask_other_item_name": "Как *называется или какой тип* товара вы продаете?",
        "preview_title_other": "📢 **Продается Товар**",
        "preview_field_other_item_name": "**Товар:** {value}",
        "btn_edit_other_item_name": "Название товара", # NEW RUSSIAN

        
        # --- Common Preview Fields ---
        "preview_field_price": "💵 **Цена:** {value}",
        "preview_field_location": "📍 **Местоположение:** {value}",
        "preview_field_description": "📝 **Описание:** {value}",
        "preview_field_no_description": "📝 **Описание:** (Описание не указано)",
        "preview_media_info_photo": "📸 Фото: {count}",
        "preview_media_info_video": "📹 Видео: {count}",
        "preview_media_info_mixed": "🖼️ Медиафайлов: {count}",
    },
    'uz': {
        # --- General & Existing ---
        "welcome": "Salom, {name}! Iltimos, tilingizni tanlang:",
        "lang_chosen": "Til O'zbek tiliga o'rnatildi.",
        "choose_category": "Nimani sotmoqchisiz?",
        "ask_price": "*Narxini* kiriting (masalan, 15000000 so'm yoki $1500).",
        "ask_location": "Mahsulot qaysi *shahar yoki tumanda* joylashgan?",
        "ask_description": "*Qisqacha tavsif* qo'shing (ixtiyoriy, maksimal {max_desc_len} belgi).\nTavsifni yuboring yoki o'tkazib yuborish uchun quyidagi tugmani bosing.",
        "ask_media": "Foto yoki video yuklang ({max_media} tagacha fayl).\nMediani yuboring, keyin quyidagi tugmalardan foydalaning.",
        "media_received": "Media qabul qilindi ({count}/{max_media}). Yana yuboring yoki 'Bajarildi' tugmasini bosing.",
        "max_media_reached": "Maksimal media fayllar soni ({max_media}) yetdi. 'Bajarildi' tugmasini bosing.",
        "no_media_uploaded_error": "Iltimos, kamida bitta foto yoki video yuklang.",
        "preview_confirm_prompt": "\n— — — — —\n\n✅ Chop etishni tasdiqlaysizmi?\nVariantni tanlang:",
        "btn_post": "✅ Chop etish", "btn_edit": "✏️ Tahrirlash", "btn_cancel": "❌ Bekor qilish",
        "post_successful_channel": "✅ {target_chat_id} kanaliga muvaffaqiyatli joylandi!",
        "post_successful_admin": "✅ E'loningiz ko'rib chiqish uchun yuborildi!",
        "post_cancelled": "Nashr bekor qilindi. /start bilan qaytadan boshlashingiz mumkin.",
        "edit_choice_prompt": "Nimani tahrirlamoqchisiz? (Eslatma: ba'zi maydonlar ushbu bo'limni qayta boshlashni talab qilishi mumkin)",
        "btn_edit_price": "💰 Narxi", 
        "btn_edit_location": "🗺️ Joylashuvi", 
        "btn_edit_description": "📄 Tavsifi", 
        "btn_edit_media": "🖼️ Media",
        "btn_back_to_preview": "↩️ Ko'rib chiqishga qaytish", 
        "btn_done_media": "✅ Yuklash Bajarildi", 
        "btn_clear_media": "🔄 Barcha Mediani Tozalash",
        "btn_skip": "➡️ O'tkazib Yuborish",
        "btn_skip_description": "➡️ Tavsifni o'tkazib yuborish",
        "description_skipped": "Tavsif o'tkazib yuborildi.", "media_cleared": "Barcha media tozalandi. Yangilarini yuklashingiz mumkin.",
        "invalid_input": "Kechirasiz, tushunmadim. Iltimos, ko'rsatmalarga amal qiling yoki tugmalardan foydalaning.",
        "price_invalid": "Narx formati noto'g'ri. Iltimos, to'g'ri narx kiriting (masalan, 150000, $1500, 150.00 EUR).",
        "description_too_long": "Tavsif juda uzun (maksimal {max_desc_len} belgi). Iltimos, qisqartiring.",
        "general_error": "Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring yoki /cancel tugmasini bosing.",
        "timeout_message": "Faoliyatsizlik tufayli suhbat vaqti tugadi. Iltimos, /start bilan qaytadan boshlang.",
        "conversation_restarted": "Avvalgi amal bekor qilindi. Keling, boshidan boshlaymiz.",
        "category_cars": "🚗 Avtomobillar", "category_houses": "🏠 Ko'chmas Mulk", "category_animals": "🐄 Hayvonlar", "category_other": "🧸 Boshqalar",
        "change_language_prompt": "Iltimos, yangi tilingizni tanlang:",
        "language_changed_success": "Til muvaffaqiyatli {new_lang_display} ga o'zgartirildi. Joriy e'lon yaratish jarayoni tiklandi. Yangi e'lon boshlash uchun /start dan foydalaning.",
        "help_message": (
            "E'lon Joylash Botiga Xush Kelibsiz!\n\n"
            "E'lonni qanday yaratish mumkin:\n"
            "1. Boshlash uchun /start dan foydalaning.\n"
            "2. Kategoriyani tanlang va tafsilotlar uchun ko'rsatmalarga amal qiling.\n"
            "3. So'ralganda foto/video yuklang.\n"
            "4. E'loningizni ko'rib chiqing, so'ngra joylashtiring, tahrirlang yoki bekor qiling.\n\n"
            "Mavjud buyruqlar:\n"
            "/start - Yangi e'lon yaratish.\n"
            "/language - Tilni o'zgartirish.\n"
            "/help - Ushbu yordam xabarini ko'rsatish.\n"
            "/cancel - Joriy e'lon yaratish jarayonini bekor qilish."
        ),
        "field_skipped": "{field_name} o'tkazib yuborildi.",

        # --- Category: Cars ---
        "category_chosen_cars": "🚗 Ajoyib! Keling, avtomobil tafsilotlarini olaylik.",
        "ask_car_make_model": "Avtomobilning *Markasi va Modeli* qanday (masalan, Toyota Camry, BMW X5)?",
        "ask_car_year": "Avtomobilning *Ishlab chiqarilgan yili* qaysi (masalan, 2018)? (Ixtiyoriy)",
        "ask_car_mileage": "Avtomobilning *Bosgan masofasi* (probegi) qancha (masalan, 55000 km)?",
        "preview_title_cars": "📢 **Avtomobil Sotiladi**",
        "preview_field_car_make_model": "**Marka/Model:** {value}",
        "preview_field_car_year": "**Yili:** {value}",
        "preview_field_car_mileage": "🛣️ **Probeg:** {value}",
        "btn_edit_car_make_model": "Marka/Modeli", # NEW UZBEK
        "btn_edit_car_year": "Yili",              # NEW UZBEK
        "btn_edit_car_mileage": "Probegi",         # NEW UZBEK
        
        # --- Category: Houses/Real Estate ---
        "category_chosen_houses": "🏠 Yaxshi! Keling, ko'chmas mulk tafsilotlarini olaylik.",
        "ask_house_property_type": "Qanday *turda ko'chmas mulk* sotyapsiz?",
        "ask_house_rooms": "Nechta *xonasi* bor (masalan, 3)? (Ixtiyoriy)",
        "ask_house_area": "Taxminiy *maydoni* qancha (masalan, 75 kv.m, 6 sotix)? (Ixtiyoriy)",
        "ask_house_year_built": "Qaysi *yili qurilgan* (masalan, 2010)? (Ixtiyoriy)",
        "property_type_apartment": "Kvartira", "property_type_house": "Hovli Uy", "property_type_land": "Yer Uchastkasi", "property_type_commercial": "Tijorat Joyi", "property_type_other": "Boshqa Tur",
        "preview_title_houses": "📢 **Ko'chmas Mulk Sotiladi**",
        "preview_field_house_property_type": "**Turi:** {value}",
        "preview_field_house_rooms": "**Xonalar soni:** {value}",
        "preview_field_house_area": "📐 **Maydoni:** {value}",
        "preview_field_house_year_built": "**Qurilgan yili:** {value}",
        "btn_edit_house_property_type": "Mulk Turi", # NEW UZBEK
        "btn_edit_house_rooms": "Xonalar Soni",     # NEW UZBEK
        "btn_edit_house_area": "Maydoni",           # NEW UZBEK
        "btn_edit_house_year_built": "Qurilgan Yili",# NEW UZBEK

        # --- Category: Animals ---
        "category_chosen_animals": "🐄 Tushunarli! Keling, hayvon haqida ma'lumot olaylik.",
        "ask_animal_type": "Qanday *hayvon* sotyapsiz (masalan, Kuchuk, Mushuk, Sigir)?",
        "ask_animal_breed": "{animal_type_placeholder}ning *zoti* qanday? (Ixtiyoriy)",
        "ask_animal_age": "Hayvonning *yoshi* qancha (masalan, 2 yosh, 6 oylik)?",
        "ask_animal_sex": "Hayvonning *jinsi* qanday? (Ixtiyoriy)",
        "animal_sex_male": "Erkak", "animal_sex_female": "Urg'ochi",
        "preview_title_animals": "📢 **Hayvon Sotiladi/Beriladi**",
        "preview_field_animal_type": "**Hayvon Turi:** {value}",
        "preview_field_animal_breed": "**Zoti:** {value}",
        "preview_field_animal_age": "**Yoshi:** {value}",
        "preview_field_animal_sex": "**Jinsi:** {value}",
        "btn_edit_animal_type": "Hayvon Turi",    # NEW UZBEK
        "btn_edit_animal_breed": "Zoti",          # NEW UZBEK
        "btn_edit_animal_age": "Yoshi",           # NEW UZBEK
        "btn_edit_animal_sex": "Jinsi",           # NEW UZBEK

        # --- Category: Other ---
        "category_chosen_other": "🧸 Bo'ldi! Keling, mahsulotingiz haqida ma'lumot olaylik.",
        "ask_other_item_name": "Sotayotgan mahsulotingizning *nomi yoki turi* nima?",
        "preview_title_other": "📢 **Mahsulot Sotiladi**",
        "preview_field_other_item_name": "**Mahsulot:** {value}",
        "btn_edit_other_item_name": "Mahsulot Nomi", # NEW UZBEK

        
        # --- Common Preview Fields ---
        "preview_field_price": "💵 **Narxi:** {value}",
        "preview_field_location": "📍 **Joylashuvi:** {value}",
        "preview_field_description": "📝 **Tavsifi:** {value}",
        "preview_field_no_description": "📝 **Tavsifi:** (Tavsif berilmagan)",
        "preview_media_info_photo": "📸 {count} ta Rasm",
        "preview_media_info_video": "📹 {count} ta Video",
        "preview_media_info_mixed": "🖼️ {count} ta Media fayl",
    }
}

def get_text(key: str, lang_code: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """Retrieves a localized string."""
    if lang_code not in SUPPORTED_LANGUAGES:
        lang_code = DEFAULT_LANGUAGE
    
    # Handle dynamic placeholders like {animal_type_placeholder}
    # This ensures that if a placeholder isn't provided, it doesn't crash .format()
    # You might want to handle this more gracefully, e.g., by having default empty strings for placeholders
    # or ensuring they are always passed. For now, this just makes it robust against missing kwargs.
    # Example: "ask_animal_breed": "What's the *breed* of the {animal_type_placeholder}? (Optional)",
    # If 'animal_type_placeholder' is not in kwargs, it will remain as {animal_type_placeholder}
    # This might be acceptable or you might want to refine it.

    text_template = strings.get(lang_code, strings[DEFAULT_LANGUAGE]).get(key, f"_{key}_")

    # Special formatting for max description length
    if key == "ask_description" or key == "description_too_long":
        from config import MAX_DESCRIPTION_LENGTH # Import here to avoid circular at top
        actual_kwargs = {'max_desc_len': MAX_DESCRIPTION_LENGTH, **kwargs}
        return text_template.format(**actual_kwargs)
    
    if key == "ask_media" or key == "media_received" or key == "max_media_reached":
        actual_kwargs = {'max_media': MAX_MEDIA_ITEMS, **kwargs}
        return text_template.format(**actual_kwargs)
        
    # For other keys, format with provided kwargs
    # If a kwarg is missing for a placeholder in the template, .format() will raise a KeyError.
    # To prevent this, you could use .format_map(defaultdict(str, **kwargs)) or similar.
    # For simplicity now, assume necessary kwargs are passed for placeholders.
    try:
        return text_template.format(**kwargs)
    except KeyError as e:
        # Log this or handle it - means a placeholder was in the string but not in kwargs
        # print(f"Warning: Missing key {e} for string '{key}' with lang '{lang_code}' and kwargs {kwargs}")
        return text_template # Return unformatted template as a fallback


def get_user_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Gets the user's selected language from context, defaults to DEFAULT_LANGUAGE."""
    return context.user_data.get('lang', DEFAULT_LANGUAGE)

def get_category_display_name(category_key: str, lang_code: str) -> str:
    """Gets the localized display name for a category key."""
    localization_key = f"category_{category_key}"
    return get_text(localization_key, lang_code)