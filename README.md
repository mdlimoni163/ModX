# Telegram Community Moderator Bot

A Python Telegram bot for community moderation:

- Filters common spam patterns automatically.
- Deletes spam messages.
- Warns repeat offenders and auto-mutes after the warning limit.
- Welcomes new members.
- Shows community rules.
- Lets users submit `/report` issues to the moderation team.
- Provides moderator-only `/warn`, `/mute`, `/unmute`, `/ban`, and `/stats`.
- Stores warnings, actions, and reports in SQLite.
- Can send escalation alerts to a separate team chat.

## 1. What you need

- A Telegram account.
- A Telegram bot token from `@BotFather`.
- Python 3.11+ OR Docker.
- A Telegram group/supergroup where you are an administrator.

## 2. Create the bot

1. Open Telegram and message `@BotFather`.
2. Run `/newbot`.
3. Choose a bot name and username.
4. Copy the bot token.
5. Optional but recommended: use `/setdescription`, `/setabouttext`, and `/setcommands`.

### Important: disable privacy mode

For a moderation bot that needs to inspect normal group messages, open `@BotFather`:

`/mybots` → select your bot → `Bot Settings` → `Group Privacy` → `Turn off`

This makes ordinary group messages available to the bot.

## 3. Add the bot to your community

Add the bot to your group/supergroup and make it an administrator.

Give it at least:

- Delete messages
- Restrict members
- Ban users
- Invite users (recommended if you later add anti-raid features)

Telegram requires the bot to be an administrator with the appropriate rights for actions such as restricting members and deleting other users' messages.

## 4. Find your group ID

A simple method:

1. Add the bot to the target group.
2. Send a message in the group.
3. Temporarily add a small debug bot/script if you need the raw `chat.id`, or use a Telegram ID utility bot.
4. Group/supergroup IDs normally look like `-100xxxxxxxxxx`.

Put that value into `TEAM_CHAT_ID` only when the team chat is a separate chat. The bot itself discovers the group ID from updates, so you do not have to hard-code the moderated group.

If you want escalation messages to go to a separate private moderator group, add this bot to that moderator group too and make it able to send messages there.

## 5. Local setup (recommended first)

### macOS / Linux

```bash
cd telegram_community_moderator

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
```

Open `.env` and at minimum change:

```env
BOT_TOKEN=YOUR_BOT_TOKEN
```

Then start:

```bash
python -m bot.main
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m bot.main
```

Keep the terminal open while the bot is running.

## 6. Test the bot

In the group, try:

```text
/rules
/help
/report Test report
```

Then send a few messages quickly, or test a duplicate message.

As an administrator, reply to a user's message and try:

```text
/warn Please avoid spam
/mute 30 repeated spam
/unmute
/ban scam attempt
```

`/stats` shows the number of open user reports stored by the bot.

## 7. Configure the spam filter

Example:

```env
SPAM_WINDOW_SECONDS=12
SPAM_MESSAGE_LIMIT=5
DUPLICATE_WINDOW_SECONDS=60
MAX_LINKS=2
MAX_MENTIONS=5
BLOCKED_WORDS=scam,phishing,free-money
```

Meaning:

- More than 5 messages in 12 seconds → spam.
- More than 2 URLs in one message → spam.
- More than 5 `@mentions` → spam.
- Repeated identical messages → spam.
- A word from `BLOCKED_WORDS` → spam.
- Extremely high capitalization → spam.

These are deliberately simple rules. Tune them for your community before using them at scale.

## 8. Team escalation

Set:

```env
TEAM_CHAT_ID=-1001234567890
```

When a user reports an issue or the automated moderation system mutes someone, the bot sends an alert to the team chat.

Recommended setup:

`Public Community` → `Moderator Bot` → `Private Moderator Team Chat`

The team chat should be invite-only.

## 9. Run with Docker

Create `.env`:

```bash
cp .env.example .env
```

Put your real token into `.env`, then:

```bash
docker compose up -d --build
```

See logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```

The SQLite database is stored in `./data`, so restarting the container does not remove moderation data.

## 10. Run tests

Install pytest:

```bash
pip install pytest
```

Then:

```bash
pytest -q
```

## 11. Project structure

```text
telegram_community_moderator/
├── bot/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── handlers.py
│   ├── main.py
│   ├── moderation.py
│   └── spam.py
├── tests/
│   └── test_spam.py
├── data/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 12. Production checklist

Before putting the bot into a busy community:

1. Disable privacy mode.
2. Promote the bot to admin.
3. Verify delete/restrict/ban permissions.
4. Configure a private team escalation chat.
5. Set `BLOCKED_WORDS` carefully.
6. Start with conservative spam thresholds.
7. Review the first few days of moderation logs.
8. Never commit `.env` or the SQLite database to GitHub.
9. Run the bot under Docker or a process supervisor so it restarts automatically.
10. Back up `data/moderator.db`.

## 13. Important Telegram limitations

The bot cannot magically moderate content it never receives. It needs the correct group configuration and administrator rights.

Message deletion and member restriction are Telegram Bot API operations with permission and timing constraints. Telegram also requires administrator rights for actions such as restricting members and deleting other users' messages.

## 14. Next upgrades

This starter is intentionally dependency-light. A production version can be extended with:

- Anti-raid join protection
- CAPTCHA / verification for new members
- Per-chat rule configuration
- Admin audit dashboard
- Redis-backed rate limiting
- PostgreSQL
- AI-assisted scam/phishing classification
- Multi-language welcome and rules
- Warning expiry
- Temporary bans
- Appeal workflow
- Moderator buttons and inline actions
- Prometheus metrics / Grafana
- Webhook deployment instead of polling
