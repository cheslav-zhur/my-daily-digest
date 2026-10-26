#!/usr/bin/env python3
"""Cron entry: wake the bot so it sends the brief, then exit."""

from __future__ import annotations

import logging
import os

import requests

WAKE_TIMEOUT_SECONDS = 120


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


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    missing = _missing_config()
    if missing:
        raise SystemExit(f"Missing {', '.join(missing)}.")
    secret = os.environ.get("CRON_SECRET", "").strip()
    url = digest_url()
    logging.info("waking %s", url)

    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {secret}"},
            timeout=WAKE_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise SystemExit(f"digest wake failed: {exc}") from exc
    if response.status_code != 200:
        raise SystemExit(f"digest wake failed: {response.status_code} {response.text}")
    logging.info("digest wake ok %s", response.status_code)


if __name__ == "__main__":
    main()
