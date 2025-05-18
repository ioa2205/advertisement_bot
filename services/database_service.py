# selling_bot/services/database_service.py
import aiosqlite
import json # Import json
import logging
from datetime import datetime
from config import DATABASE_NAME, DEFAULT_LANGUAGE
from constants import CAT_SPECIFIC_DATA_KEY # Import the key

logger = logging.getLogger(__name__)

async def init_db():
    """Initializes the database and creates/alters tables if they don't exist."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # Check if 'category_specific_data' column exists in posts table
        cursor = await db.execute("PRAGMA table_info(posts)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'category_specific_data' not in columns:
            try:
                await db.execute("ALTER TABLE posts ADD COLUMN category_specific_data TEXT")
                logger.info("Column 'category_specific_data' added to 'posts' table.")
            except aiosqlite.OperationalError as e:
                # This might happen if the table needs to be recreated, or other schema issues.
                # For a simple setup, we might log and continue, assuming it might be created next.
                logger.warning(f"Could not add 'category_specific_data' column, might already exist or other issue: {e}")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_lang TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT,  -- <--- This is the problem part if it's NOT NULL implicitly or explicitly by some DBs/modes
                price TEXT,
                location TEXT,
                description TEXT,
                media_files TEXT,
                category_specific_data TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                channel_message_id INTEGER
            )
        """)
        # Users table remains the same
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                lang_code TEXT,
                first_name TEXT,
                username TEXT,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    logger.info("Database initialized/checked successfully.")

async def save_post(user_data: dict) -> int:
    """Saves the post data to the database, including category-specific data."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # Serialize category_specific_data to JSON string
        category_specific_json = json.dumps(user_data.get(CAT_SPECIFIC_DATA_KEY, {}))
        
        # Determine 'title'. If a specific primary field exists (e.g., car_make_model),
        # that might be used as a de facto title, or keep a generic one.
        # For this implementation, we'll assume 'title' might be None if not explicitly asked for
        # and the preview formatter handles displaying the primary identifier.
        # Let's ensure 'title', 'price', 'location', 'description' are fetched with .get() for safety.

        cursor = await db.execute(
            """
            INSERT INTO posts (user_id, user_lang, category, 
                               price, location, description, media_files, 
                               category_specific_data, status, title) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_data['user_id'],
                user_data.get('lang', DEFAULT_LANGUAGE), # Ensure lang is present
                user_data['category'],
                user_data.get('price'), # Common field
                user_data.get('location'), # Common field
                user_data.get('description'), # Common field
                json.dumps(user_data.get('media_files', [])),
                category_specific_json, # New field
                'pending',
                user_data.get('title') # Generic title, might be null or derived from specific data
            )
        )
        await db.commit()
        post_id = cursor.lastrowid
        logger.info(f"Post {post_id} saved for user {user_data['user_id']}. Specific data: {category_specific_json}")
        return post_id

async def update_post_status(post_id: int, status: str, channel_message_id: int = None):
    """Updates the status of a post and optionally its channel_message_id."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        if channel_message_id:
            await db.execute("UPDATE posts SET status = ?, channel_message_id = ? WHERE id = ?", (status, channel_message_id, post_id))
        else:
            await db.execute("UPDATE posts SET status = ? WHERE id = ?", (status, post_id))
        await db.commit()
        logger.info(f"Post {post_id} status updated to {status}.")

async def get_user_pref_lang(user_id: int) -> str | None:
    """Retrieves the user's preferred language from the users table."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT lang_code FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_user_pref_lang(user_id: int, lang_code: str, first_name: str, username: str | None):
    """Sets or updates the user's preferred language and info in the users table."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, lang_code, first_name, username, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            lang_code = excluded.lang_code,
            first_name = excluded.first_name,
            username = excluded.username,
            last_seen = excluded.last_seen
            """,
            (user_id, lang_code, first_name, username, datetime.now())
        )
        await db.commit()
        logger.info(f"User {user_id} language preference set to {lang_code}.")