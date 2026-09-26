from __future__ import annotations

from typing import Literal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from digest.content.news.period import NEWS_PERIODS, NewsPeriod, coerce_period
from digest.content.news.topics import NEWS_GROUPS, NEWS_TOPICS, TOPIC_BY_ID

# Compact callback_data under Telegram's 64-byte limit (KTD1).
_PREFIX = "nh"
CALLBACK_OPEN = f"{_PREFIX}:open"

_PERIOD_BUTTON_RU: dict[NewsPeriod, str] = {
    "day": "День",
    "week": "Неделя",
    "month": "Месяц",
}

HubAction = Literal["open", "topic", "period"]


def encode_open() -> str:
    return CALLBACK_OPEN


def encode_topic(topic_id: str) -> str:
    return f"{_PREFIX}:t:{topic_id}"


def encode_period(topic_id: str, period: NewsPeriod) -> str:
    return f"{_PREFIX}:p:{topic_id}:{period}"


def decode_callback(
    data: str,
) -> tuple[HubAction, str | None, NewsPeriod | None] | None:
    """Parse hub callback_data. Returns (action, topic_id, period) or None."""
    parts = data.split(":")
    if len(parts) < 2 or parts[0] != _PREFIX:
        return None
    kind = parts[1]
    if kind == "open" and len(parts) == 2:
        return ("open", None, None)
    if kind == "t" and len(parts) == 3:
        topic_id = parts[2]
        if topic_id not in TOPIC_BY_ID:
            return None
        return ("topic", topic_id, None)
    if kind == "p" and len(parts) == 4:
        topic_id, period_raw = parts[2], parts[3]
        if topic_id not in TOPIC_BY_ID:
            return None
        try:
            period = coerce_period(period_raw)
        except ValueError:
            return None
        return ("period", topic_id, period)
    return None


def topic_keyboard() -> InlineKeyboardMarkup:
    """Topic choices in NEWS_GROUPS / NEWS_TOPICS order."""
    by_id = {t.id: t for t in NEWS_TOPICS}
    rows: list[list[InlineKeyboardButton]] = []
    for group in NEWS_GROUPS:
        row: list[InlineKeyboardButton] = []
        for topic_id in group.topic_ids:
            topic = by_id[topic_id]
            row.append(
                InlineKeyboardButton(
                    topic.label.rstrip(":"),
                    callback_data=encode_topic(topic.id),
                )
            )
            # Keep rows short: 2 buttons per row for readability.
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
    return InlineKeyboardMarkup(rows)


def topic_ids_on_keyboard(markup: InlineKeyboardMarkup) -> list[str]:
    ids: list[str] = []
    for row in markup.inline_keyboard:
        for button in row:
            decoded = decode_callback(button.callback_data or "")
            if decoded is not None and decoded[0] == "topic" and decoded[1]:
                ids.append(decoded[1])
    return ids


def period_keyboard(topic_id: str) -> InlineKeyboardMarkup:
    row = [
        InlineKeyboardButton(
            _PERIOD_BUTTON_RU[period],
            callback_data=encode_period(topic_id, period),
        )
        for period in NEWS_PERIODS
    ]
    return InlineKeyboardMarkup([row])


def brief_entry_keyboard() -> InlineKeyboardMarkup:
    """Single «Новости» button attached to the scheduled brief (R5)."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Новости", callback_data=encode_open())]]
    )


HUB_INTRO_HTML = "<b>📰 Новости</b>\nВыбери тему:"
PERIOD_PROMPT_HTML = "<b>📰 {topic}</b>\nВыбери период:"
