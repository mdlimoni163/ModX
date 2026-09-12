from bot.spam import SpamEngine

def build(**overrides):
    cfg = dict(
        window_seconds=12,
        message_limit=5,
        duplicate_window_seconds=60,
        max_links=2,
        max_mentions=5,
        blocked_words={"scam"},
    )
    cfg.update(overrides)
    return SpamEngine(**cfg)

def test_blocked_word():
    e = build()
    assert e.check(1, "this is a scam").is_spam

def test_too_many_links():
    e = build()
    assert e.check(1, "https://a.com https://b.com https://c.com").is_spam

def test_duplicate():
    e = build()
    e.check(1, "hello everyone")
    assert e.check(1, "hello   everyone").is_spam

def test_caps():
    e = build()
    assert e.check(1, "THIS MESSAGE IS WAY TOO LOUD").is_spam

def test_flood():
    e = build(message_limit=2)
    assert not e.check(1, "one").is_spam
    assert not e.check(1, "two").is_spam
    assert e.check(1, "three").is_spam
