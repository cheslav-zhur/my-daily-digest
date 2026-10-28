#!/usr/bin/env python3
"""Cron entry: wake the bot so it sends the brief, then exit."""

from __future__ import annotations

import logging
import os
import sys
import time

import requests

WAKE_TIMEOUT_SECONDS = 120
WAKE_ATTEMPTS = 18
WAKE_RETRY_DELAY_SECONDS = 10
RETRYABLE_STATUS = frozenset({502, 503})


def digest_url() -> str:
    explicit = os.environ.get("DIGEST_URL", "").strip()
    if explicit:
        return explicit
    host = os.environ.get("BOT_PRIVATE_DOMAIN", "").strip()
    port = os.environ.get("BOT_PORT", "").strip()
    if not host or not port:
        return ""
    return f"http://{host}:{port}/cron/digest"


def _missing_config() -> list[str]:
    missing: list[str] = []
    if not os.environ.get("CRON_SECRET", "").strip():
        missing.append("CRON_SECRET")
    if os.environ.get("DIGEST_URL", "").strip():
        return missing
    if not os.environ.get("BOT_PRIVATE_DOMAIN", "").strip():
        missing.append("BOT_PRIVATE_DOMAIN")
    if not os.environ.get("BOT_PORT", "").strip():
        missing.append("BOT_PORT")
    return missing


def _post_digest(url: str, secret: str) -> requests.Response:
    return requests.post(
        url,
        headers={"Authorization": f"Bearer {secret}"},
        timeout=WAKE_TIMEOUT_SECONDS,
    )


def wake(url: str, secret: str) -> None:
    """POST /cron/digest, retrying while the sleeping bot cold-boots."""
    last_error = "unknown error"
    for attempt in range(1, WAKE_ATTEMPTS + 1):
        try:
            response = _post_digest(url, secret)
        except requests.RequestException as exc:
            last_error = str(exc)
            logging.info(
                "wake attempt %s/%s failed: %s",
                attempt,
                WAKE_ATTEMPTS,
                last_error,
            )
        else:
            if response.status_code == 200:
                logging.info("digest wake ok %s", response.status_code)
                return
            last_error = f"{response.status_code} {response.text}"
            if response.status_code not in RETRYABLE_STATUS:
                raise SystemExit(f"digest wake failed: {last_error}")
            logging.info(
                "wake attempt %s/%s failed: %s",
                attempt,
                WAKE_ATTEMPTS,
                last_error,
            )
        if attempt < WAKE_ATTEMPTS:
            time.sleep(WAKE_RETRY_DELAY_SECONDS)
    raise SystemExit(f"digest wake failed: {last_error}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    missing = _missing_config()
    if missing:
        raise SystemExit(f"Missing {', '.join(missing)}.")
    secret = os.environ.get("CRON_SECRET", "").strip()
    url = digest_url()
    logging.info("waking %s", url)
    wake(url, secret)


if __name__ == "__main__":
    main()
