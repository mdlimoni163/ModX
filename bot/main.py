import logging
from telegram import BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters,
)

from .config import load_settings
from .database import Database
from .spam import SpamEngine
from .handlers import (
    command_start,
    command_rules,
    command_help,
    command_report,
    command_warn,
    command_mute,
    command_unmute,
    command_ban,
    command_stats,
    on_new_members,
    on_text_message,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help"),
        BotCommand("rules", "Show community rules"),
        BotCommand("report", "Report an issue to moderators"),
        BotCommand("warn", "Warn a user (moderators)"),
        BotCommand("mute", "Mute a user (moderators)"),
        BotCommand("unmute", "Unmute a user (moderators)"),
        BotCommand("ban", "Ban a user (moderators)"),
        BotCommand("stats", "Show moderation stats"),
    ])

def build_app():
    settings = load_settings()
    db = Database(settings.database_path)
    spam = SpamEngine(
        window_seconds=settings.spam_window_seconds,
        message_limit=settings.spam_message_limit,
        duplicate_window_seconds=settings.duplicate_window_seconds,
        max_links=settings.max_links,
        max_mentions=settings.max_mentions,
        blocked_words=settings.blocked_words,
    )

    app = Application.builder().token(settings.bot_token).post_init(post_init).build()
    app.bot_data["settings"] = settings
    app.bot_data["db"] = db
    app.bot_data["spam"] = spam

    app.add_handler(CommandHandler("start", command_start))
    app.add_handler(CommandHandler("help", command_help))
    app.add_handler(CommandHandler("rules", command_rules))
    app.add_handler(CommandHandler("report", command_report))
    app.add_handler(CommandHandler("warn", command_warn))
    app.add_handler(CommandHandler("mute", command_mute))
    app.add_handler(CommandHandler("unmute", command_unmute))
    app.add_handler(CommandHandler("ban", command_ban))
    app.add_handler(CommandHandler("stats", command_stats))

    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_members)
    )
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            on_text_message,
        )
    )
    app.add_handler(
        MessageHandler(
            filters.CaptionRegex(r".+") & ~filters.COMMAND,
            on_text_message,
        )
    )
    # ChatMemberHandler is intentionally omitted for minimal permissions.
    return app

def main():
    app = build_app()
    logger.info("Starting Telegram community moderator...")
    app.run_polling(allowed_updates=None)

if __name__ == "__main__":
    main()
