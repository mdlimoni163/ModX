import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

def _csv_set(name: str) -> set[str]:
    raw = os.getenv(name, "")
    return {x.strip().lower() for x in raw.split(",") if x.strip()}

def _csv_int_set(name: str) -> set[int]:
    raw = os.getenv(name, "")
    out = set()
    for x in raw.split(","):
        x = x.strip()
        if x:
            out.add(int(x))
    return out

@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_path: str = "data/moderator.db"
    team_chat_id: int | None = None
    log_chat_id: int | None = None
    language: str = "en"
    warn_limit: int = 3
    mute_minutes: int = 60
    spam_window_seconds: int = 12
    spam_message_limit: int = 5
    duplicate_window_seconds: int = 60
    max_links: int = 2
    max_mentions: int = 5
    blocked_words: set[str] = field(default_factory=set)
    trusted_user_ids: set[int] = field(default_factory=set)
    welcome_text: str = (
        "Welcome, {name}! 👋\n\n"
        "Please read /rules before posting. "
        "Be respectful, avoid spam, and use /report if you need moderator help."
    )
    rules_text: str = (
        "📜 Community Rules\n\n"
        "1. Be respectful and do not harass others.\n"
        "2. No spam, scams, phishing, or malicious links.\n"
        "3. No flooding, repeated messages, or excessive mentions.\n"
        "4. Keep discussions relevant to the community.\n"
        "5. Follow moderator instructions.\n\n"
        "Use /report <reason> to contact the moderation team."
    )

def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is required in .env")

    team_chat = os.getenv("TEAM_CHAT_ID", "").strip()
    log_chat = os.getenv("LOG_CHAT_ID", "").strip()

    return Settings(
        bot_token=token,
        database_path=os.getenv("DATABASE_PATH", "data/moderator.db"),
        team_chat_id=int(team_chat) if team_chat else None,
        log_chat_id=int(log_chat) if log_chat else None,
        warn_limit=int(os.getenv("WARN_LIMIT", "3")),
        mute_minutes=int(os.getenv("MUTE_MINUTES", "60")),
        spam_window_seconds=int(os.getenv("SPAM_WINDOW_SECONDS", "12")),
        spam_message_limit=int(os.getenv("SPAM_MESSAGE_LIMIT", "5")),
        duplicate_window_seconds=int(os.getenv("DUPLICATE_WINDOW_SECONDS", "60")),
        max_links=int(os.getenv("MAX_LINKS", "2")),
        max_mentions=int(os.getenv("MAX_MENTIONS", "5")),
        blocked_words=_csv_set("BLOCKED_WORDS"),
        trusted_user_ids=_csv_int_set("TRUSTED_USER_IDS"),
        welcome_text=os.getenv(
            "WELCOME_TEXT",
            "Welcome, {name}! 👋\n\nPlease read /rules before posting. "
            "Be respectful, avoid spam, and use /report <reason> if you need moderator help."
        ),
        rules_text=os.getenv(
            "RULES_TEXT",
            "📜 Community Rules\n\n"
            "1. Be respectful and do not harass others.\n"
            "2. No spam, scams, phishing, or malicious links.\n"
            "3. No flooding, repeated messages, or excessive mentions.\n"
            "4. Keep discussions relevant to the community.\n"
            "5. Follow moderator instructions.\n\n"
            "Use /report <reason> to contact the moderation team."
        ),
    )
