# Telegram Ad Posting Bot

A multi-lingual, conversational Telegram bot that helps users create and post "for sale" advertisements in a structured, step-by-step format. It supports various categories (e.g., Cars, Real Estate, Animals, Other) with category-specific questions, media uploads, and a review step before publishing to a designated Telegram channel or notifying an admin.

![image](https://github.com/IbodulloGaffarov/reklama_bot/assets/99054365/20b69fd4-b7c2-4f0d-b0a9-e43b7137989a)


## ✨ Features

*   **Conversational Interface:** Guides users step-by-step through ad creation.
*   **Multi-Language Support:** Currently supports English, Russian, and Uzbek. Easily extensible.
*   **Category-Specific Questions:** Asks relevant questions based on the selected ad category (Cars, Real Estate, Animals, Other).
*   **Media Uploads:** Allows users to upload multiple photos and/or videos for their ads (up to 10).
*   **Preview & Edit:** Users can review their ad and edit specific fields before final submission.
*   **Channel Posting / Admin Notification:** Configurable to post ads directly to a Telegram channel or notify an administrator.
*   **Persistent Storage:** Uses SQLite to store submitted ads and user language preferences.
*   **Input Validation:** Basic validation for fields like price, year, mileage, etc.
*   **Global Commands:**
    *   `/start`: Initiates or restarts the ad creation process.
    *   `/language`: Allows users to change their preferred language at any time.
    *   `/help`: Provides usage instructions.
    *   `/cancel`: Cancels the current ad creation process.

## 🚀 Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   Python 3.9+
*   pip (Python package installer)
*   Git

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ioa2205/advertisement_bot.git
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    ```
    Activate it:
    *   Windows: `.venv\Scripts\activate`
    *   macOS/Linux: `source .venv/bin/activate`

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the Bot:**
    *   Rename `config.py.example` to `config.py` (if you provide an example file) OR create `config.py` in the project root.
    *   Open `config.py` and fill in the necessary details:
        ```python
        BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Get this from BotFather on Telegram
        
        # Target for posting:
        # If IS_CHANNEL is True, TARGET_CHAT_ID should be the channel username (e.g., "@mychannelname") or channel ID (e.g., -1001234567890)
        # If IS_CHANNEL is False, TARGET_CHAT_ID should be an admin's numerical user_id for direct notification
        TARGET_CHAT_ID = "YOUR_TARGET_CHAT_ID"  # e.g., "@your_channel" or your personal numerical user_id
        IS_CHANNEL = True # Set to False if TARGET_CHAT_ID is an admin's user_id

        DATABASE_NAME = "ads_bot.db"
        DEFAULT_LANGUAGE = 'en'
        # ... (other configurations like CATEGORIES_KEYS, MAX_MEDIA_ITEMS are usually fine as default)
        ```
    *   **Important:**
        *   Get your `BOT_TOKEN` by talking to [BotFather](https://t.me/botfather) on Telegram.
        *   If posting to a channel, ensure your bot is an **administrator in that channel with permission to post messages.**
        *   To get a numerical User ID (for admin notifications), message `@userinfobot` on Telegram.
        *   To get a numerical Channel ID (for private channels), you might need to temporarily make it public, use a bot like `@username_to_id_bot`, then make it private again.

### Running the Bot Locally

```bash
python main.py
```
Use code with caution.
Markdown
Or, if main.py is part of a package (e.g., inside a selling_bot directory):
python -m selling_bot.main
Use code with caution.
Bash
The bot should now be running and responding to commands on Telegram.
🛠️ Project Structure
reklama_bot/
```
│
├── .venv/                   # Virtual environment (if used)
├── database/
│   └── schema.sql           # Reference SQL schema (not used at runtime)
├── handlers/
│   └── conversation_flow.py # Core conversation logic and state transitions
├── services/
│   ├── database_service.py  # SQLite operations
│   └── message_formatter.py # Dynamic ad text formatting
├── __pycache__/             # Compiled Python files (usually ignored)
├── config.py                # Bot configuration (token, target chat ID, etc.)
├── constants.py             # Constants for state management, callbacks, etc.
├── localization.py          # Internationalization and multilingual UI strings
├── main.py                  # Entry point: sets up handlers and runs the bot
├── requirements.txt         # List of Python dependencies
├── ads_bot.db               # SQLite database file (created at runtime)
└── README.md                # You're reading it!
```

📝 License
This project can be licensed under the MIT License - see the LICENSE.md file for details (if you choose to add one).
