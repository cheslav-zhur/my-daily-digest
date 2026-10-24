# Testing

`pytest`. Dev dependencies live in `requirements-dev.txt` (kept out of the prod
`requirements.txt` — Railway never installs them). Tests live in `tests/`,
mirroring the `digest/` package. CI runs `pytest` on push and PR
(`.github/workflows/tests.yml`).

## Running

```bash
pip install -r requirements-dev.txt
pytest
```

## What we test

- **The pure core, not I/O.** Parsing (`digest/content/news/parse.py`), HTML
  assembly (`digest/content/telegram_html.py`, `digest/content/report.py`), and
  prompt building (`digest/content/news/prompt.py`).
- **Not** the fetchers or real HTTP calls — the contract there is "whatever the
  API returns". The only nod to that boundary is captured sonar payloads used as
  fixtures.

## Conventions

- **Property assertions, not exact block snapshots.** Assert on number of links,
  whitelist membership, no raw URLs leaking into summaries, tags closed — not on
  byte-for-byte output. This stays resilient to cosmetic LLM-output changes while
  still catching real regressions.
- **Characterization-first for existing code:** capture current behavior before
  refactoring. If a test reveals a latent bug, flag it — don't silently assert
  the bug as expected.
- **Test-first for new behavior** that has a pure function to pin down.
- **Fixtures:** sonar responses live as JSON under `tests/fixtures/`.
- **Code comments, docstrings, and these docs are in English.**
- The `NewsTopic` factory lives in `tests/conftest.py`.
