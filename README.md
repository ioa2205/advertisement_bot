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
    git clone https://github.com/[Your GitHub Username]/[Your Repo Name].git
    cd [Your Repo Name]
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
│
├── .venv/                    # Virtual environment (if used)
├── database/
│   └── schema.sql            # Reference SQL schema (not used at runtime for data storage)
├── handlers/
│   └── conversation_flow.py  # Core conversation logic, state handlers
├── services/
│   ├── database_service.py   # SQLite database interactions
│   └── message_formatter.py  # Formats ad previews and posts
├── __pycache__/              # Python cache files (usually in .gitignore)
├── config.py                 # Bot configuration (BOT_TOKEN, TARGET_CHAT_ID, etc.)
├── constants.py              # State identifiers, callback prefixes, constant values
├── localization.py           # Multi-language strings and i18n functions
├── main.py                   # Main application entry point
├── requirements.txt          # Python dependencies
├── ads_bot.db                # SQLite database file (created at runtime)
└── README.md                 # This file
🔧 Key Components Explained
main.py: Initializes the python-telegram-bot application, sets up handlers, and starts the bot's polling loop.
handlers/conversation_flow.py: Contains the primary ConversationHandler for ad posting and a secondary one for language changes. It defines all states and the logic for transitioning between them based on user input.
services/database_service.py: Manages all interactions with the SQLite database (ads_bot.db), including table creation, saving posts, and managing user language preferences. Category-specific ad details are stored as a JSON blob.
services/message_formatter.py: Responsible for constructing the text for ad previews and final posts, dynamically including category-specific fields.
localization.py: Provides all UI text in supported languages. New languages can be added by extending the strings dictionary.
constants.py: Centralizes all state identifiers, callback data prefixes, and other fixed values to ensure consistency and avoid magic strings/numbers.
config.py: Stores essential configuration parameters. For deployment, sensitive values like BOT_TOKEN should ideally be moved to environment variables.
☁️ Deployment
This bot can be deployed to various cloud platforms that support Python applications. Here are a few suggestions with free tiers:
Railway.app: Recommended for ease of use. Supports Git-based deployment, Procfile (for worker: python main.py), and environment variables.
Render.com: Another good option with a free tier for web services or background workers. Free web services may "spin down."
Fly.io: Offers a generous free tier and global infrastructure, good for performance. Uses Docker and flyctl.
General Deployment Steps (e.g., for Railway):
Prepare for Git: Ensure your project is a Git repository and pushed to GitHub/GitLab.
Procfile: Create a Procfile in the root: worker: python main.py
runtime.txt: (Optional) Create runtime.txt: python-3.11.5 (or your version).
Environment Variables: Modify config.py to read sensitive values (BOT_TOKEN, TARGET_CHAT_ID) from environment variables (e.g., using os.environ.get()).
Platform Setup:
Sign up for Railway (or chosen platform).
Create a new project and deploy from your Git repository.
Set the required environment variables in the platform's dashboard.
Monitor deployment and runtime logs.
💡 Future Enhancements & To-Do
Advanced Edit Flow: Allow editing of all category-specific fields with a more dynamic menu.
"Back" Button: Implement a "back" functionality during the ad creation steps.
Robust Input Validation: Add more specific validation for all input fields (numeric ranges, formats, etc.).
Saved Drafts: Allow users to save and resume incomplete ads.
Admin Panel/Commands: For moderation, viewing pending ads (if an approval flow is added), user management.
Unit/Integration Tests: Improve code reliability.
Persistence for Conversation State: Use PicklePersistence to allow conversations to survive bot restarts.
User Feedback/Rating System: (More complex)
Image Processing: Option to compress or resize uploaded images.
🙏 Contributing
Contributions, issues, and feature requests are welcome! Please feel free to check [issues page](https://github.com/[Your GitHub Username]/[Your Repo Name]/issues) if you want to contribute.
📝 License
This project can be licensed under the MIT License - see the LICENSE.md file for details (if you choose to add one).
