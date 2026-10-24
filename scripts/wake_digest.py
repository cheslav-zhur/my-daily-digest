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


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    secret = os.environ.get("CRON_SECRET", "").strip()
    url = digest_url()
    if not secret or not url:
        raise SystemExit("CRON_SECRET and the bot address are required.")

    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {secret}"},
        timeout=WAKE_TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise SystemExit(f"digest wake failed: {response.status_code} {response.text}")
    logging.info("digest wake ok")


if __name__ == "__main__":
    main()
