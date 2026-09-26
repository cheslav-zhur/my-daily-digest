"""Tests for optional reply_markup on Telegram delivery helpers."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from digest.telegram.delivery import _send_telegram_message_async
from digest.telegram.news_hub import brief_entry_keyboard


def test_send_passes_reply_markup_on_html_path() -> None:
    markup = brief_entry_keyboard()
    bot = MagicMock()
    bot.send_message = AsyncMock(return_value=None)

    with patch("digest.telegram.delivery.Bot", return_value=bot):
        asyncio.run(
            _send_telegram_message_async(
                "1",
                "token",
                "<b>hi</b>",
                reply_markup=markup,
            )
        )

    bot.send_message.assert_awaited_once()
    kwargs = bot.send_message.await_args.kwargs
    assert kwargs["reply_markup"] is markup
    assert kwargs["parse_mode"] == "HTML"
