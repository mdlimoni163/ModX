import html
import logging
from telegram import Update, ChatMember
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes

from .moderation import is_admin, mute, unmute
from .spam import SpamEngine

logger = logging.getLogger(__name__)

def display_name(user) -> str:
    return html.escape(user.full_name or user.username or str(user.id))

async def log_team(context, text: str):
    chat_id = context.application.bot_data["settings"].team_chat_id
    if chat_id:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        except Exception:
            logger.exception("Could not send team message")

async def log_chat(context, text: str):
    chat_id = context.application.bot_data["settings"].log_chat_id
    if chat_id:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        except Exception:
            logger.exception("Could not send log message")

async def command_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "👋 I’m the community moderation bot.\n\n"
        "/rules — community rules\n"
        "/help — command help\n"
        "/report <reason> — contact moderators"
    )

async def command_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = context.application.bot_data["settings"]
    await update.effective_message.reply_text(settings.rules_text)

async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "User commands:\n"
        "/start /help /rules /report <reason>\n\n"
        "Moderator commands (reply to a user's message):\n"
        "/warn [reason]\n"
        "/mute [minutes] [reason]\n"
        "/unmute\n"
        "/ban [reason]\n"
        "/unban (reply to a user's message if supported by your Telegram client)\n"
        "/stats\n\n"
        "The bot automatically checks messages for spam and suspicious patterns."
    )

async def command_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    reason = " ".join(context.args).strip() if context.args else ""
    if not reason:
        await message.reply_text("Usage: /report <reason>")
        return

    db = context.application.bot_data["db"]
    report_id = db.add_report(
        update.effective_chat.id,
        update.effective_user.id,
        message.message_id,
        reason,
    )
    await message.reply_text("✅ Report received. The moderation team has been notified.")

    await log_team(
        context,
        f"🚨 <b>New report #{report_id}</b>\n"
        f"Chat: <code>{update.effective_chat.id}</code>\n"
        f"User: <code>{update.effective_user.id}</code> ({display_name(update.effective_user)})\n"
        f"Reason: {html.escape(reason)}",
    )

async def command_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not update.effective_chat or not update.effective_user:
        return
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return
    target = await _target_or_reply(message)
    if not target:
        await message.reply_text("Reply to a user’s message to warn them.")
        return
    if await is_admin(context.bot, update.effective_chat.id, target.id):
        await message.reply_text("I won’t warn an administrator.")
        return

    reason = " ".join(context.args).strip() or "Community guidelines"
    db = context.application.bot_data["db"]
    db.add_warning(update.effective_chat.id, target.id, update.effective_user.id, reason)
    count = db.warning_count(update.effective_chat.id, target.id)
    settings = context.application.bot_data["settings"]

    await message.reply_text(f"⚠️ Warning issued to {target.full_name}. ({count}/{settings.warn_limit})")
    db.log_action(update.effective_chat.id, target.id, update.effective_user.id, "warn", reason)

    if count >= settings.warn_limit:
        await mute(context.bot, update.effective_chat.id, target.id, settings.mute_minutes)
        db.log_action(update.effective_chat.id, target.id, update.effective_user.id, "auto_mute", "warning limit")
        await message.reply_text(
            f"🔇 {target.full_name} has reached the warning limit and was muted for {settings.mute_minutes} minutes."
        )

    await log_team(
        context,
        f"⚠️ Warn: <code>{target.id}</code> by <code>{update.effective_user.id}</code> — {html.escape(reason)}"
    )

async def command_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _moderator_only(update, context):
        return
    target = await _target_or_reply(update.effective_message)
    if not target:
        await update.effective_message.reply_text("Reply to a user’s message to mute them.")
        return
    if await is_admin(context.bot, update.effective_chat.id, target.id):
        await update.effective_message.reply_text("I won’t mute an administrator.")
        return

    minutes = context.application.bot_data["settings"].mute_minutes
    reason_parts = context.args[:]
    if reason_parts and reason_parts[0].isdigit():
        minutes = max(1, min(int(reason_parts[0]), 10080))
        reason_parts = reason_parts[1:]
    reason = " ".join(reason_parts).strip() or "Community guidelines"

    await mute(context.bot, update.effective_chat.id, target.id, minutes)
    context.application.bot_data["db"].log_action(
        update.effective_chat.id, target.id, update.effective_user.id, "mute", reason
    )
    await update.effective_message.reply_text(
        f"🔇 {target.full_name} muted for {minutes} minutes."
    )
    await log_team(
        context,
        f"🔇 Mute: <code>{target.id}</code> by <code>{update.effective_user.id}</code> for {minutes}m — {html.escape(reason)}"
    )

async def command_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _moderator_only(update, context):
        return
    target = await _target_or_reply(update.effective_message)
    if not target:
        await update.effective_message.reply_text("Reply to a user’s message to unmute them.")
        return
    await unmute(context.bot, update.effective_chat.id, target.id)
    context.application.bot_data["db"].log_action(
        update.effective_chat.id, target.id, update.effective_user.id, "unmute"
    )
    await update.effective_message.reply_text(f"🔊 {target.full_name} can speak again.")

async def command_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _moderator_only(update, context):
        return
    target = await _target_or_reply(update.effective_message)
    if not target:
        await update.effective_message.reply_text("Reply to a user’s message to ban them.")
        return
    if await is_admin(context.bot, update.effective_chat.id, target.id):
        await update.effective_message.reply_text("I won’t ban an administrator.")
        return

    reason = " ".join(context.args).strip() or "Community guidelines"
    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    context.application.bot_data["db"].log_action(
        update.effective_chat.id, target.id, update.effective_user.id, "ban", reason
    )
    await update.effective_message.reply_text(f"⛔ {target.full_name} has been banned.")
    await log_team(
        context,
        f"⛔ Ban: <code>{target.id}</code> by <code>{update.effective_user.id}</code> — {html.escape(reason)}"
    )

async def command_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _moderator_only(update, context):
        return
    db = context.application.bot_data["db"]
    count = db.open_report_count(update.effective_chat.id)
    await update.effective_message.reply_text(f"📊 Open reports: {count}")

async def on_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.new_chat_members:
        return
    settings = context.application.bot_data["settings"]
    for user in message.new_chat_members:
        if user.is_bot:
            continue
        welcome = settings.welcome_text.format(name=user.full_name)
        await message.reply_text(welcome)

async def on_member_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Reserved for future join/leave auditing.
    pass

async def on_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat:
        return
    if chat.type not in {"group", "supergroup"}:
        return
    if user.id in context.application.bot_data["settings"].trusted_user_ids:
        return

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
            return
    except Exception:
        logger.exception("Could not determine member status")
        return

    text = message.text or message.caption or ""
    if not text:
        return

    engine: SpamEngine = context.application.bot_data["spam"]
    decision = engine.check(user.id, text)
    if not decision.is_spam:
        return

    try:
        await message.delete()
    except Exception:
        logger.exception("Failed to delete spam message")

    db = context.application.bot_data["db"]
    db.log_action(chat.id, user.id, context.bot.id, "delete_spam", decision.reason)

    warning_id = db.add_warning(chat.id, user.id, context.bot.id, f"Automated spam filter: {decision.reason}")
    count = db.warning_count(chat.id, user.id)
    settings = context.application.bot_data["settings"]

    try:
        await message.reply_text(
            f"⚠️ {user.mention_html()} your message was removed: {html.escape(decision.reason)}",
            parse_mode="HTML",
        )
    except Exception:
        pass

    if count >= settings.warn_limit:
        try:
            await mute(context.bot, chat.id, user.id, settings.mute_minutes)
            db.log_action(chat.id, user.id, context.bot.id, "auto_mute", decision.reason)
            await log_team(
                context,
                f"🤖 Auto-mute after spam warning #{warning_id}: "
                f"<code>{user.id}</code> ({html.escape(user.full_name)}) — {html.escape(decision.reason)}"
            )
        except Exception:
            logger.exception("Failed auto-mute")

async def _moderator_only(update, context) -> bool:
    if not update.effective_chat or not update.effective_user:
        return False
    allowed = await is_admin(context.bot, update.effective_chat.id, update.effective_user.id)
    if not allowed:
        await update.effective_message.reply_text("Only chat administrators can use this command.")
    return allowed

async def _target_or_reply(message):
    return message.reply_to_message.from_user if message.reply_to_message else None
