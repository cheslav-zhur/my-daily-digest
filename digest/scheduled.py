from __future__ import annotations

import os

from digest.content.service import DigestSection, build_digest_delivery
from digest.observability import flush_observability
from digest.telegram.delivery import send_telegram_message
from digest.telegram.news_hub import brief_entry_keyboard
from digest.trace_source import set_trace_source


def scheduled_sections() -> tuple[DigestSection, ...]:
    """Cron and local scheduled runs send only the brief (news is on-demand)."""
    return (DigestSection.BRIEF,)


def deliver_scheduled_digest(*, source: str = "local") -> None:
    """Send the scheduled brief only; news is requested via the bot hub."""
    set_trace_source(source)
    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not telegram_bot_token or not telegram_chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required.")

    news_markup = brief_entry_keyboard()
    for section in scheduled_sections():
        delivery = build_digest_delivery(section)
        for html_text in delivery.messages:
            send_telegram_message(
                chat_id=telegram_chat_id,
                bot_token=telegram_bot_token,
                html_text=html_text,
                reply_markup=news_markup if section == DigestSection.BRIEF else None,
            )
    flush_observability()
