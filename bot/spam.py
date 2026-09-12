import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass

URL_RE = re.compile(r"(https?://|www\.)\S+", re.I)
MENTION_RE = re.compile(r"@\w+")
WORD_RE = re.compile(r"[a-zA-Z0-9_]+")

@dataclass
class SpamDecision:
    is_spam: bool
    reason: str = ""

class SpamEngine:
    def __init__(
        self,
        window_seconds: int,
        message_limit: int,
        duplicate_window_seconds: int,
        max_links: int,
        max_mentions: int,
        blocked_words: set[str],
    ):
        self.window_seconds = window_seconds
        self.message_limit = message_limit
        self.duplicate_window_seconds = duplicate_window_seconds
        self.max_links = max_links
        self.max_mentions = max_mentions
        self.blocked_words = blocked_words
        self.messages = defaultdict(deque)
        self.last_text = {}

    @staticmethod
    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def check(self, user_id: int, text: str) -> SpamDecision:
        now = time.monotonic()
        q = self.messages[user_id]
        while q and now - q[0] > self.window_seconds:
            q.popleft()
        q.append(now)

        normalized = self.normalize(text)
        previous = self.last_text.get(user_id)
        self.last_text[user_id] = (now, normalized)

        if len(q) > self.message_limit:
            return SpamDecision(True, "message flood")

        links = len(URL_RE.findall(text))
        if links > self.max_links:
            return SpamDecision(True, "too many links")

        mentions = len(MENTION_RE.findall(text))
        if mentions > self.max_mentions:
            return SpamDecision(True, "too many mentions")

        words = set(w.lower() for w in WORD_RE.findall(text))
        matched = self.blocked_words.intersection(words)
        if matched:
            return SpamDecision(True, f"blocked keyword: {sorted(matched)[0]}")

        if previous:
            prev_time, prev_text = previous
            if normalized and normalized == prev_text and now - prev_time <= self.duplicate_window_seconds:
                return SpamDecision(True, "duplicate message")

        letters = [c for c in text if c.isalpha()]
        if len(letters) >= 20:
            upper_ratio = sum(c.isupper() for c in letters) / len(letters)
            if upper_ratio >= 0.92:
                return SpamDecision(True, "excessive capitalization")

        return SpamDecision(False)
