"""Pure tests for which digest sections a scheduled run sends."""

from __future__ import annotations

from digest.content.service import DigestSection
from digest.scheduled import scheduled_sections


def test_scheduled_sections_always_brief_only() -> None:
    assert scheduled_sections() == (DigestSection.BRIEF,)
