"""Characterization tests for topic prompt assembly."""

from __future__ import annotations

from digest.content.news.parse import MAX_TOPIC_LINKS
from digest.content.news.prompt import build_topic_prompt


def test_build_topic_prompt_includes_date_and_search_brief(make_topic) -> None:
    topic = make_topic(search_brief="latest robotics news")
    prompt = build_topic_prompt(topic, "2026-06-13")

    assert "2026-06-13" in prompt
    assert "latest robotics news" in prompt


def test_build_topic_prompt_carries_output_scaffold(make_topic) -> None:
    prompt = build_topic_prompt(make_topic(), "2026-06-13")

    assert "SUMMARY:" in prompt
    assert "LINK:" in prompt
    # The link cap from parse.py must flow into the prompt instructions.
    assert str(MAX_TOPIC_LINKS) in prompt


def test_build_topic_prompt_week_mentions_week_window(make_topic) -> None:
    prompt = build_topic_prompt(make_topic(), "2026-06-13", period="week")
    lower = prompt.lower()

    assert "time window: last week" in lower
    assert "prefer sources and events inside the last week" in lower


def test_build_topic_prompt_month_mentions_month_window(make_topic) -> None:
    prompt = build_topic_prompt(make_topic(), "2026-06-13", period="month")

    assert "month" in prompt.lower()
    assert "last month" in prompt.lower() or "past month" in prompt.lower()
