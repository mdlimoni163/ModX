import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class Database:
    def __init__(self, path: str):
        self.path = path
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._init()

    @contextmanager
    def conn(self):
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _init(self):
        with self.conn() as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER,
                moderator_id INTEGER,
                action TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                reporter_id INTEGER NOT NULL,
                message_id INTEGER,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open'
            );
            """)

    def add_warning(self, chat_id, user_id, moderator_id, reason) -> int:
        with self.conn() as con:
            cur = con.execute(
                "INSERT INTO warnings(chat_id,user_id,moderator_id,reason,created_at) VALUES(?,?,?,?,?)",
                (chat_id, user_id, moderator_id, reason, utc_now()),
            )
            return cur.lastrowid

    def warning_count(self, chat_id, user_id) -> int:
        with self.conn() as con:
            row = con.execute(
                "SELECT COUNT(*) AS n FROM warnings WHERE chat_id=? AND user_id=?",
                (chat_id, user_id),
            ).fetchone()
            return int(row["n"])

    def log_action(self, chat_id, user_id, moderator_id, action, reason=""):
        with self.conn() as con:
            con.execute(
                "INSERT INTO actions(chat_id,user_id,moderator_id,action,reason,created_at) VALUES(?,?,?,?,?,?)",
                (chat_id, user_id, moderator_id, action, reason, utc_now()),
            )

    def add_report(self, chat_id, reporter_id, message_id, reason) -> int:
        with self.conn() as con:
            cur = con.execute(
                "INSERT INTO reports(chat_id,reporter_id,message_id,reason,created_at) VALUES(?,?,?,?,?)",
                (chat_id, reporter_id, message_id, reason, utc_now()),
            )
            return cur.lastrowid

    def open_report_count(self, chat_id) -> int:
        with self.conn() as con:
            row = con.execute(
                "SELECT COUNT(*) AS n FROM reports WHERE chat_id=? AND status='open'",
                (chat_id,),
            ).fetchone()
            return int(row["n"])
