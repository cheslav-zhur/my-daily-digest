"""Tests for period → OpenRouter recency and single-topic fetch helpers."""

from __future__ import annotations

from digest.content.news.fetch import _chat_extra, resolve_topic
from digest.content.news.period import NEWS_PERIODS


def test_chat_extra_day_sets_day_recency() -> None:
    assert _chat_extra("day")["search_recency_filter"] == "day"


def test_chat_extra_week_sets_week_recency() -> None:
    assert _chat_extra("week")["search_recency_filter"] == "week"


def test_chat_extra_month_sets_month_recency() -> None:
    assert _chat_extra("month")["search_recency_filter"] == "month"


def test_news_periods_are_day_week_month() -> None:
    assert NEWS_PERIODS == ("day", "week", "month")


def test_resolve_topic_accepts_id_and_topic(make_topic) -> None:
    topic = make_topic(id="ai")
    assert resolve_topic(topic) is topic
    assert resolve_topic("ai").id == "ai"
