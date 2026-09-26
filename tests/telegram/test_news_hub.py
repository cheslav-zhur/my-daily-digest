"""Pure tests for news hub keyboard and callback helpers."""

from __future__ import annotations

from types import SimpleNamespace

from digest.content.news.topics import NEWS_TOPICS
from digest.telegram.handlers import is_authorized
from digest.telegram.news_hub import (
    CALLBACK_OPEN,
    brief_entry_keyboard,
    decode_callback,
    encode_open,
    encode_period,
    encode_topic,
    period_keyboard,
    topic_ids_on_keyboard,
    topic_keyboard,
)


def test_callback_encode_decode_topic_round_trip() -> None:
    data = encode_topic("ai")
    assert decode_callback(data) == ("topic", "ai", None)


def test_callback_encode_decode_period_round_trip() -> None:
    data = encode_period("geopolitics", "week")
    assert decode_callback(data) == ("period", "geopolitics", "week")
    assert len(data.encode("utf-8")) <= 64


def test_callback_encode_open() -> None:
    assert decode_callback(encode_open()) == ("open", None, None)
    assert encode_open() == CALLBACK_OPEN


def test_topic_keyboard_lists_each_topic_once() -> None:
    ids = topic_ids_on_keyboard(topic_keyboard())
    expected = [t.id for t in NEWS_TOPICS]
    assert ids == expected
    assert len(ids) == len(set(ids))


def test_period_keyboard_carries_topic_id() -> None:
    markup = period_keyboard("crypto")
    payloads = [
        btn.callback_data
        for row in markup.inline_keyboard
        for btn in row
    ]
    assert encode_period("crypto", "day") in payloads
    assert encode_period("crypto", "week") in payloads
    assert encode_period("crypto", "month") in payloads


def test_brief_entry_keyboard_opens_same_hub() -> None:
    markup = brief_entry_keyboard()
    assert len(markup.inline_keyboard) == 1
    assert len(markup.inline_keyboard[0]) == 1
    button = markup.inline_keyboard[0][0]
    assert button.text == "Новости"
    assert button.callback_data == encode_open()


def test_decode_rejects_unknown_payload() -> None:
    assert decode_callback("other:stuff") is None
    assert decode_callback("nh:p:ai:year") is None
    assert decode_callback("nh:t:not-a-topic") is None
    assert decode_callback("nh:p:not-a-topic:day") is None


def test_unauthorized_user_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_USER_ID", "111")
    update = SimpleNamespace(effective_user=SimpleNamespace(id=222))
    assert is_authorized(update) is False


def test_authorized_user_matches_env(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_USER_ID", "111")
    update = SimpleNamespace(effective_user=SimpleNamespace(id=111))
    assert is_authorized(update) is True
