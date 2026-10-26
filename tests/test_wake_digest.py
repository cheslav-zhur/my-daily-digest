from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from scripts.wake_digest import digest_url, main


def test_digest_url_uses_private_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DIGEST_URL", raising=False)
    monkeypatch.setenv("BOT_PRIVATE_DOMAIN", "bot.railway.internal")
    monkeypatch.setenv("BOT_PORT", "8080")

    assert digest_url() == "http://bot.railway.internal:8080/cron/digest"


def test_digest_url_prefers_explicit_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DIGEST_URL", "http://bot/cron/digest")
    monkeypatch.setenv("BOT_PRIVATE_DOMAIN", "ignored.internal")
    monkeypatch.setenv("BOT_PORT", "1")

    assert digest_url() == "http://bot/cron/digest"


def test_main_posts_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("CRON_SECRET", "s3cret")
    monkeypatch.setenv("DIGEST_URL", "http://bot/cron/digest")
    response = MagicMock(status_code=200, text="ok")

    with (
        caplog.at_level(logging.INFO),
        patch("scripts.wake_digest.requests.post", return_value=response) as post,
    ):
        main()

    assert "waking http://bot/cron/digest" in caplog.text
    assert "digest wake ok 200" in caplog.text

    post.assert_called_once_with(
        "http://bot/cron/digest",
        headers={"Authorization": "Bearer s3cret"},
        timeout=120,
    )


def test_main_exits_when_bot_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "s3cret")
    monkeypatch.setenv("DIGEST_URL", "http://bot/cron/digest")
    response = MagicMock(status_code=500, text="error")

    with (
        patch("scripts.wake_digest.requests.post", return_value=response),
        pytest.raises(SystemExit, match="digest wake failed: 500"),
    ):
        main()


def test_main_exits_without_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "s3cret")
    monkeypatch.delenv("DIGEST_URL", raising=False)
    monkeypatch.delenv("BOT_PRIVATE_DOMAIN", raising=False)
    monkeypatch.delenv("BOT_PORT", raising=False)

    with pytest.raises(SystemExit, match=r"^Missing BOT_PRIVATE_DOMAIN, BOT_PORT\.$"):
        main()


def test_main_names_empty_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "s3cret")
    monkeypatch.delenv("DIGEST_URL", raising=False)
    monkeypatch.setenv("BOT_PRIVATE_DOMAIN", "bot.railway.internal")
    monkeypatch.setenv("BOT_PORT", "  ")

    with pytest.raises(SystemExit, match=r"^Missing BOT_PORT\.$"):
        main()
