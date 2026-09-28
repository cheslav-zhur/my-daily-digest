"""Tests for period → OpenRouter recency and single-topic fetch helpers."""

from __future__ import annotations

from unittest.mock import patch

from digest.content.news.fetch import (
    TopicNewsResult,
    _chat_extra,
    fetch_topic_news,
    resolve_topic,
)
from digest.content.news.period import NEWS_PERIODS


def test_chat_extra_day_sets_day_recency() -> None:
    assert _chat_extra("day")["search_recency_filter"] == "day"


def test_chat_extra_week_sets_week_recency() -> None:
    assert _chat_extra("week")["search_recency_filter"] == "week"


def test_chat_extra_month_sets_month_recency() -> None:
    assert _chat_extra("month")["search_recency_filter"] == "month"


def test_chat_extra_caps_completion_tokens() -> None:
    """OpenRouter reserves max_tokens against the balance; sonar's default is 65536."""
    for period in NEWS_PERIODS:
        assert _chat_extra(period)["max_tokens"] == 1024


def test_news_periods_are_day_week_month() -> None:
    assert NEWS_PERIODS == ("day", "week", "month")


def test_resolve_topic_accepts_id_and_topic(make_topic) -> None:
    topic = make_topic(id="ai")
    assert resolve_topic(topic) is topic
    assert resolve_topic("ai").id == "ai"


def test_fetch_topic_news_no_key_returns_failure(make_topic) -> None:
    with patch("digest.content.news.fetch.openrouter_api_key", return_value=""):
        result = fetch_topic_news(make_topic(), "2026-06-13", period="week")

    assert isinstance(result, TopicNewsResult)
    assert result.text is None
    assert result.failure_reason == "no key"
    assert result.period == "week"


def test_fetch_topic_news_success_wraps_block(make_topic) -> None:
    topic = make_topic()
    with (
        patch("digest.content.news.fetch.openrouter_api_key", return_value="sk"),
        patch(
            "digest.content.news.fetch._fetch_topic_block",
            return_value=("ИИ:\nok", 0.01, None),
        ),
    ):
        result = fetch_topic_news(topic, "2026-06-13", period="day")

    assert result.text == "ИИ:\nok"
    assert result.failure_reason is None
    assert result.cost == 0.01
