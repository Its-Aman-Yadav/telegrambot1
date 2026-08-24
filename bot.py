import logging
import asyncio
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatMember,
    constants
)
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

import config
import database

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Valid member statuses in Telegram
SUBSCRIBED_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
    ChatMemberStatus.RESTRICTED
}


async def is_user_subscribed(bot, user_id: int) -> bool:
    """Checks whether a user is currently a member of the required channel."""
    if not config.CHANNEL_ID:
        return True

    try:
        chat_member: ChatMember = await bot.get_chat_member(
            chat_id=config.CHANNEL_ID,
            user_id=user_id
        )
        return chat_member.status in SUBSCRIBED_STATUSES
    except Exception as e:
        logger.error(f"Error checking membership for user {user_id} in {config.CHANNEL_ID}: {e}")
        # Note: If the bot is not admin in the channel, get_chat_member will fail.
        # We will inform the logs clearly.
        return False


def get_force_sub_keyboard(payload: Optional[str] = None) -> InlineKeyboardMarkup:
    """Generates the inline keyboard with premium 'Join VIP Channel' and 'Verify' buttons."""
    check_data = f"check_sub:{payload}" if payload else "check_sub"
    keyboard = [
        [
            InlineKeyboardButton(
                text="👑 ᴊᴏɪɴ ᴠɪᴘ ᴄʜᴀɴɴᴇʟ 🍿",
                url=config.CHANNEL_INVITE_LINK
            )
        ],
        [
            InlineKeyboardButton(
                text="⚡ ᴠᴇʀɪꜰʏ & ᴜɴʟᴏᴄᴋ ᴍᴏᴠɪᴇ 🔓",
                callback_data=check_data
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def send_force_sub_message(update: Update, payload: Optional[str] = None):
    """Sends the forced subscription notification in an ultra-premium layout."""
    link = config.CHANNEL_INVITE_LINK

    text = (
        "👑 **𝐔𝐋𝐓𝐈𝐌𝐀𝐓𝐄 𝐂𝐈𝐍𝐄𝐌𝐀 𝐇𝐔𝐁** 👑\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🍿 *Watch & Download in Ultra HD 4K*\n\n"
        "⚡️ **𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗩𝗜𝗣 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗕𝗲𝗹𝗼𝘄:**\n"
        f"➪ {link}\n"
        f"➪ {link}\n"
        f"➪ {link}\n"
        f"➪ {link}\n"
        f"➪ {link}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚜️ *Multi-Audio: English | हिंदी | & More* 🇮🇳\n"
        "💎 *Unlimited Movies & Web-Series for Free*\n\n"
        "⚠️ **To get your movie, you MUST join the channel above!**\n"
        "After joining, click **'⚡ ᴠᴇʀɪꜰʏ & ᴜɴʟᴏᴄᴋ ᴍᴏᴠɪᴇ 🔓'** below."
    )

    keyboard = get_force_sub_keyboard(payload)

    if update.callback_query:
        await update.callback_query.message.reply_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    elif update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )


async def deliver_movie(update: Update, context: ContextTypes.DEFAULT_TYPE, movie: dict):
    """Delivers movie file or download links to the user."""
    chat_id = update.effective_chat.id
    title = movie.get("title", "Movie")
    description = movie.get("description", "")
    file_id = movie.get("file_id")
    file_type = movie.get("file_type", "document")
    download_url = movie.get("download_url")
    poster_url = movie.get("poster_url")

    caption = f"🎬 **{title}**\n\n"
    if description:
        caption += f"📝 {description}\n\n"
    caption += "🍿 *Enjoy your movie!*"

    buttons = []
    if download_url:
        buttons.append([InlineKeyboardButton("🔗 Download / Watch Online", url=download_url)])
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    # Send movie via stored file_id if available
    if file_id:
        try:
            if file_type == "video":
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=file_id,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=file_id,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            return
        except Exception as e:
            logger.error(f"Failed to send movie file_id: {e}")

    # If poster is available without direct file
    if poster_url:
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=poster_url,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        except Exception as e:
            logger.error(f"Failed to send poster: {e}")

    # Fallback to plain text message
    await context.bot.send_message(
        chat_id=chat_id,
        text=caption,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command and deep-linking payloads."""
    user = update.effective_user
    if not user:
        return

    database.add_or_update_user(user.id, user.username, user.first_name)

    # Extract deep link payload (e.g. /start movie_123)
    payload = context.args[0] if context.args else None

    # 1. Force Subscription Check
    is_subbed = await is_user_subscribed(context.bot, user.id)
    if not is_subbed:
        await send_force_sub_message(update, payload=payload)
        return

    # 2. User is subscribed
    if payload:
        # Check if payload corresponds to a movie code or ID
        movie = database.get_movie_by_code(payload)
        if not movie and payload.isdigit():
            movie = database.get_movie_by_id(int(payload))

        if movie:
            await deliver_movie(update, context, movie)
            return
        else:
            await update.message.reply_text(
                "❌ **Movie not found or link expired.**\n"
                "Please search for the movie title by typing its name in this chat.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

    # 3. Default Welcome Message
    keyboard = [
        [
            InlineKeyboardButton("🔍 Search Movies", callback_data="btn_search"),
            InlineKeyboardButton("🔥 Latest Movies", callback_data="btn_latest")
        ],
        [
            InlineKeyboardButton("ℹ️ How to Use", callback_data="btn_help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 **Welcome to the Movies Bot, {user.first_name}!**\n\n"
        "🍿 You can search and download your favorite movies right here.\n\n"
        "🔎 **How to search:** Simply send the name of any movie in this chat!\n"
        "Example: `Inception` or `Avatar`"
    )

    await update.message.reply_text(
        text=welcome_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button clicks (Try Again, Search, Latest, etc.)."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user = update.effective_user

    # Handle subscription re-check
    if data.startswith("check_sub"):
        parts = data.split(":", 1)
        payload = parts[1] if len(parts) > 1 else None

        is_subbed = await is_user_subscribed(context.bot, user.id)
        if not is_subbed:
            await query.answer(
                "❌ You have not joined the channel yet! Please join first.",
                show_alert=True
            )
            return

        # User has joined successfully!
        await query.answer("✅ Verification successful! Access granted.", show_alert=False)
        try:
            await query.message.delete()
        except Exception:
            pass

        if payload:
            movie = database.get_movie_by_code(payload)
            if not movie and payload.isdigit():
                movie = database.get_movie_by_id(int(payload))
            if movie:
                await deliver_movie(update, context, movie)
                return

        # Send welcome message if no specific payload
        keyboard = [
            [
                InlineKeyboardButton("🔍 Search Movies", callback_data="btn_search"),
                InlineKeyboardButton("🔥 Latest Movies", callback_data="btn_latest")
            ]
        ]
        await query.message.reply_text(
            f"🎉 **Thank you for joining!**\n\n"
            f"You now have full access to our movie library.\n"
            f"Send me the name of any movie to find it!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    elif data == "btn_search":
        await query.message.reply_text(
            "🔎 **Search Movies:**\n\n"
            "Just type and send any movie name (e.g. `Spider-Man`, `Interstellar`) in this chat!",
            parse_mode=ParseMode.MARKDOWN
        )

    elif data == "btn_latest":
        movies = database.get_latest_movies(limit=8)
        if not movies:
            await query.message.reply_text("🎬 No movies added yet. Check back soon!")
            return

        buttons = []
        for m in movies:
            buttons.append([InlineKeyboardButton(f"🎬 {m['title']}", callback_data=f"get_movie:{m['id']}")])

        await query.message.reply_text(
            "🔥 **Latest Movies:**\nSelect a movie to get it:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN
        )

    elif data.startswith("get_movie:"):
        movie_id = int(data.split(":")[1])
        # Re-verify membership before delivery
        if not await is_user_subscribed(context.bot, user.id):
            await send_force_sub_message(update)
            return

        movie = database.get_movie_by_id(movie_id)
        if movie:
            await deliver_movie(update, context, movie)
        else:
            await query.message.reply_text("❌ Movie not found.")

    elif data == "btn_help":
        help_text = (
            "📖 **Help & Instructions:**\n\n"
            "1. Make sure you are subscribed to our official channel.\n"
            "2. Type any movie title in the chat to search.\n"
            "3. Click on the result to get the movie file or download link instantly!\n\n"
            "💡 Need help? Contact channel admins."
        )
        await query.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text messages from users (acts as movie search)."""
    user = update.effective_user
    if not user or not update.message or not update.message.text:
        return

    database.add_or_update_user(user.id, user.username, user.first_name)

    # 1. Force Subscription Check
    if not await is_user_subscribed(context.bot, user.id):
        await send_force_sub_message(update)
        return

    query = update.message.text.strip()
    if query.startswith("/"):
        return  # Ignore unrecognized commands

    # Search database for matching movies
    results = database.search_movies(query, limit=8)
    if not results:
        await update.message.reply_text(
            f"❌ No movies found matching '`{query}`'.\n"
            "Please check the spelling or try searching another title.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    buttons = []
    for m in results:
        buttons.append([InlineKeyboardButton(f"🎬 {m['title']}", callback_data=f"get_movie:{m['id']}")])

    await update.message.reply_text(
        f"🔍 **Search results for** '`{query}`':\n"
        "Click below to get your movie:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )


# ==================== ADMIN COMMANDS ====================

def is_admin(user_id: int) -> bool:
    """Checks if the user is an admin."""
    return config.ADMIN_ID != 0 and user_id == config.ADMIN_ID


async def add_movie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to manually add a movie link/entry."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    # Syntax: /addmovie <Title> | <Download_URL> | <Description>
    text = " ".join(context.args) if context.args else ""
    if not text or "|" not in text:
        await update.message.reply_text(
            "ℹ️ **Format:** `/addmovie Title | Download_URL | Description (optional)`\n\n"
            "Example:\n"
            "`/addmovie Inception (2010) | https://example.com/dl/inception.mp4 | Sci-fi Mind-bending Thriller`\n\n"
            "💡 *Tip:* You can also directly forward any video/file to this bot to save it as a movie!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    parts = [p.strip() for p in text.split("|")]
    title = parts[0]
    download_url = parts[1] if len(parts) > 1 else None
    description = parts[2] if len(parts) > 2 else ""

    movie_id = database.add_movie(
        title=title,
        download_url=download_url,
        description=description
    )

    movie = database.get_movie_by_id(movie_id)
    bot_me = await context.bot.get_me()
    share_link = f"https://t.me/{bot_me.username}?start={movie['movie_code']}"

    await update.message.reply_text(
        f"✅ **Movie Added Successfully!**\n\n"
        f"🎬 **Title:** {title}\n"
        f"🔗 **Deep-Link:** `{share_link}`\n\n"
        f"Users clicking that link will be forced to join the channel before receiving the movie.",
        parse_mode=ParseMode.MARKDOWN
    )


async def admin_file_receiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows admins to send/forward videos or documents to save directly to the bot."""
    user = update.effective_user
    if not is_admin(user.id):
        return

    message = update.message
    file_id = None
    file_type = "document"
    title = "Untitled Movie"

    if message.video:
        file_id = message.video.file_id
        file_type = "video"
        title = message.video.file_name or message.caption or "Movie Video"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
        title = message.document.file_name or message.caption or "Movie File"

    if not file_id:
        return

    # Use caption as description if provided
    description = message.caption or ""

    movie_id = database.add_movie(
        title=title,
        file_id=file_id,
        file_type=file_type,
        description=description
    )

    movie = database.get_movie_by_id(movie_id)
    bot_me = await context.bot.get_me()
    share_link = f"https://t.me/{bot_me.username}?start={movie['movie_code']}"

    await message.reply_text(
        f"✅ **Movie File Saved!**\n\n"
        f"🎬 **Title:** {title}\n"
        f"📁 **Type:** {file_type.capitalize()}\n"
        f"🔗 **Share Link:** `{share_link}`",
        parse_mode=ParseMode.MARKDOWN
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to view bot statistics."""
    user = update.effective_user
    if not is_admin(user.id):
        return

    users_count = database.get_user_count()
    movies_count = database.get_movie_count()

    await update.message.reply_text(
        f"📊 **Bot Statistics:**\n\n"
        f"👥 **Total Users:** {users_count}\n"
        f"🎬 **Total Movies:** {movies_count}\n"
        f"📢 **Channel Target:** `{config.CHANNEL_ID}`",
        parse_mode=ParseMode.MARKDOWN
    )


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to broadcast a message to all users."""
    user = update.effective_user
    if not is_admin(user.id):
        return

    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("ℹ️ Usage: `/broadcast <your message>`", parse_mode=ParseMode.MARKDOWN)
        return

    users = database.get_all_users()
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(f"📤 Broadcasting to {len(users)} users...")

    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=text, parse_mode=ParseMode.MARKDOWN)
            sent += 1
            await asyncio.sleep(0.05)  # Telegram rate-limiting protection
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ **Broadcast Finished!**\n\n"
        f"✔️ Sent: {sent}\n"
        f"❌ Failed/Blocked: {failed}",
        parse_mode=ParseMode.MARKDOWN
    )


async def post_init(application: Application):
    """Sets bot description before user clicks start."""
    try:
        desc = (
            "👑 𝐔𝐋𝐓𝐈𝐌𝐀𝐓𝐄 𝐂𝐈𝐍𝐄𝐌𝐀 𝐇𝐔𝐁 👑\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🍿 ᴡᴀᴛᴄʜ & ᴅᴏᴡɴʟᴏᴀᴅ ɪɴ ᴜʟᴛʀᴀ ʜᴅ 4ᴋ\n\n"
            "⚡️ 𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗩𝗜𝗣 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗕𝗲𝗹𝗼𝘄:\n"
            f"➪ {config.CHANNEL_INVITE_LINK}\n"
            f"➪ {config.CHANNEL_INVITE_LINK}\n"
            f"➪ {config.CHANNEL_INVITE_LINK}\n"
            f"➪ {config.CHANNEL_INVITE_LINK}\n"
            f"➪ {config.CHANNEL_INVITE_LINK}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⚜️ ᴍᴜʟᴛɪ-ᴀᴜᴅɪᴏ: ᴇɴɢʟɪsʜ | हिंदी | & ᴍᴏʀᴇ 🇮🇳\n"
            "💎 ᴜɴʟɪᴍɪᴛᴇᴅ ᴍᴏᴠɪᴇꜱ & ᴡᴇʙ-ꜱᴇʀɪᴇꜱ"
        )
        await application.bot.set_my_description(desc)
        await application.bot.set_my_short_description("👑 ULTIMATE CINEMA HUB - Watch Movies in 4K")
        logger.info("Bot description updated successfully.")
    except Exception as e:
        logger.warning(f"Could not set bot description: {e}")


def main():
    """Initializes and runs the bot."""
    # Check config validity
    errors = config.validate_config()
    if errors:
        print("=" * 60)
        print("⚠️  CONFIGURATION WARNING:")
        for err in errors:
            print(f"  • {err}")
        print("=" * 60)

    # Initialize SQLite database
    database.init_db()

    if not config.BOT_TOKEN or config.BOT_TOKEN == "your_bot_token_here":
        print("❌ Cannot start bot without a valid BOT_TOKEN. Exiting.")
        return

    # Build Application
    app = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("addmovie", add_movie_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Admin file uploader handler (video or document)
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, admin_file_receiver))

    # Text search handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    logger.info("Bot started successfully. Listening for updates...")
    print("🚀 Movies Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
