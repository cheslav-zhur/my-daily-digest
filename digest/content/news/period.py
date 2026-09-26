from __future__ import annotations

from typing import Literal

NewsPeriod = Literal["day", "week", "month"]

NEWS_PERIODS: tuple[NewsPeriod, ...] = ("day", "week", "month")

# English window phrases injected into the OpenRouter prompt (KTD2).
_PERIOD_WINDOW_EN: dict[NewsPeriod, str] = {
    "day": "last 24 hours",
    "week": "last week",
    "month": "last month",
}

_PERIOD_SUMMARY_SCOPE_EN: dict[NewsPeriod, str] = {
    "day": "the main news of the day",
    "week": "the main news of the week",
    "month": "the main news of the month",
}

# Russian empty-result copy shown to the user.
_PERIOD_NO_NEWS_RU: dict[NewsPeriod, str] = {
    "day": "За 24 часа новостей нет.",
    "week": "За неделю новостей нет.",
    "month": "За месяц новостей нет.",
}

_PERIOD_LABEL_RU: dict[NewsPeriod, str] = {
    "day": "день",
    "week": "неделя",
    "month": "месяц",
}


def coerce_period(value: str) -> NewsPeriod:
    if value not in NEWS_PERIODS:
        raise ValueError(f"unknown news period: {value!r}")
    return value  # type: ignore[return-value]


def period_window_en(period: NewsPeriod) -> str:
    return _PERIOD_WINDOW_EN[period]


def period_summary_scope_en(period: NewsPeriod) -> str:
    return _PERIOD_SUMMARY_SCOPE_EN[period]


def no_news_text(period: NewsPeriod = "day") -> str:
    return _PERIOD_NO_NEWS_RU[period]


def period_label_ru(period: NewsPeriod) -> str:
    return _PERIOD_LABEL_RU[period]
