from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
import requests

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


def test_main_retries_connection_refused_then_ok(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("CRON_SECRET", "s3cret")
    monkeypatch.setenv("DIGEST_URL", "http://bot/cron/digest")
    refused = requests.ConnectionError("Connection refused")
    ok = MagicMock(status_code=200, text="ok")

    with (
        caplog.at_level(logging.INFO),
        patch("scripts.wake_digest.time.sleep") as sleep,
        patch(
            "scripts.wake_digest.requests.post",
            side_effect=[refused, refused, ok],
        ) as post,
    ):
        main()

    assert post.call_count == 3
    assert sleep.call_count == 2
    sleep.assert_called_with(10)
    assert "wake attempt 1/18 failed: Connection refused" in caplog.text
    assert "digest wake ok 200" in caplog.text


def test_main_retries_502_then_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "s3cret")
    monkeypatch.setenv("DIGEST_URL", "http://bot/cron/digest")
    bad_gateway = MagicMock(status_code=502, text="Bad Gateway")
    ok = MagicMock(status_code=200, text="ok")

    with (
        patch("scripts.wake_digest.time.sleep"),
        patch(
            "scripts.wake_digest.requests.post",
            side_effect=[bad_gateway, ok],
        ) as post,
    ):
        main()

    assert post.call_count == 2


def test_main_exits_when_bot_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "s3cret")
    monkeypatch.setenv("DIGEST_URL", "http://bot/cron/digest")
    response = MagicMock(status_code=500, text="error")

    with (
        patch("scripts.wake_digest.requests.post", return_value=response) as post,
        pytest.raises(SystemExit, match="digest wake failed: 500"),
    ):
        main()

    post.assert_called_once()


def test_main_exits_after_retries_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "s3cret")
    monkeypatch.setenv("DIGEST_URL", "http://bot/cron/digest")
    refused = requests.ConnectionError("Connection refused")

    with (
        patch("scripts.wake_digest.WAKE_ATTEMPTS", 3),
        patch("scripts.wake_digest.time.sleep") as sleep,
        patch("scripts.wake_digest.requests.post", side_effect=refused) as post,
        pytest.raises(SystemExit, match="digest wake failed: Connection refused"),
    ):
        main()

    assert post.call_count == 3
    assert sleep.call_count == 2


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
