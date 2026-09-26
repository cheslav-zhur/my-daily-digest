"""Pure tests for which digest sections a scheduled run sends."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from digest.content.service import DigestSection
from digest.scheduled import deliver_scheduled_digest, scheduled_sections
from digest.telegram.news_hub import encode_open


def test_scheduled_sections_always_brief_only() -> None:
    assert scheduled_sections() == (DigestSection.BRIEF,)


def test_deliver_scheduled_digest_attaches_news_button(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    send = MagicMock()
    delivery = MagicMock()
    delivery.messages = ["<b>brief</b>"]

    with (
        patch("digest.scheduled.build_digest_delivery", return_value=delivery),
        patch("digest.scheduled.send_telegram_message", send),
        patch("digest.scheduled.flush_observability"),
    ):
        deliver_scheduled_digest(source="test")

    send.assert_called_once()
    kwargs = send.call_args.kwargs
    assert kwargs["html_text"] == "<b>brief</b>"
    markup = kwargs["reply_markup"]
    assert markup.inline_keyboard[0][0].callback_data == encode_open()
