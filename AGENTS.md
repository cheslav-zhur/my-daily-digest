# AGENTS.md

## Project

**Daily Digest Bot** — a personal morning briefing in Telegram.

GitHub Actions hits `POST /cron/digest` on Railway **twice a day**; assembly and delivery happen on the server:

- Weather in Da Nang
- Rates: BTC, ETH, VND/USD
- Motivation

News is **not** sent by cron: only on request through the «Новости» hub (button under the brief, or `/news`) — topic → period → one LLM call.

**Stack:** Python 3.11+, GitHub Actions, Railway (webhook + Serverless), OpenRouter (`perplexity/sonar`), Langfuse (optional), Telegram Bot API, wttr.in, CoinGecko.

**No database** — every run is stateless.

**Setup and secrets:** see [`SETUP.md`](SETUP.md).

**Project layout:** see [`STRUCTURE.md`](STRUCTURE.md).

## GitHub

- **Repo:** https://github.com/happylolonly/my-daily-digest

## Run modes

| Mode | Entry point | Where it runs |
|------|-------------|---------------|
| Morning and evening: brief only (+ «Новости» button) | `POST /cron/digest` | GitHub Actions → Railway |
| Commands `/brief`, `/news`, … | `python bot.py` | Railway (webhook) or locally (polling) |

**Bot mode:** if `WEBHOOK_URL` or `RAILWAY_PUBLIC_DOMAIN` + `WEBHOOK_SECRET` is set → webhook; otherwise polling.

## News (hot path)

**11 topics, 3 groups** (catalog for the hub; one topic is fetched per request):

| Group | Topics |
|-------|--------|
| Technology | AI, Crypto, Technology, Robotics |
| World | Economy, Geopolitics, Dubai, Singapore, Vietnam |
| Politics | War (RU–UA), Belarus |

```
/news or the «Новости» button
  → topic keyboard → period (day/week/month)
  → fetch_topic_news(topic, date, period)
  → 1× OpenRouter (perplexity/sonar, 30s timeout, search_recency_filter)
  → parse + build_single_topic_news_html → message + topic keyboard again
```

## Telegram delivery

Cron / `/brief` — **1 message**: date, weather, rates, motivation; the cron brief includes an inline «Новости» button (no news LLM call).

`/news` opens the topic hub (no fetch). After a period is chosen — **1 message** for that topic; an empty or failed request gets a clear reply for that topic only.

RSS (`fetchers/news.py`) and Gemini (`llm.py`) are in the repo but **are not called** from `service.py`.

## Idiomatic Python

- **Functions, not classes** — each data source is one function `fetch_*() -> str | None`
- **`dataclasses`** — for data passed between layers
- **`os.environ`** — config from env; local `.env` via `python-dotenv` in dev only
- **`logging`**, not `print`
- **`requests`** with an explicit `timeout` (fetchers: 10s; OpenRouter: 30s)
- **Type hints** on public functions
- **stdlib first** — skip extra dependencies (OpenRouter via `requests`, not an SDK)

## Tests

Conventions and how to run: see [`TESTING.md`](TESTING.md). In short: `pytest`, tests in `tests/`, dev dependencies in `requirements-dev.txt` (not in prod).

## Code rules

1. **Graceful degradation** — each fetch in its own `try/except`; one failed news topic does not take down the hub
2. **Telegram HTML** — only `<b>` and `<a href>` in news; `parse_mode=HTML`
3. **VND/USD** — a separate forex API, not CoinGecko
4. **News** — plain text from the model; HTML is assembled in `report.py`
5. **Citations** — URL whitelist from `citations`, `search_results`, `message.annotations` (OpenRouter)

## Secrets

See [`SETUP.md`](SETUP.md). In short:

- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `OPENROUTER_API_KEY` — required on Railway
- `CRON_SECRET` — GitHub Actions + Railway (`Authorization: Bearer`)
- `RAILWAY_PUBLIC_DOMAIN` — in GitHub secrets for the cron workflow
- `TELEGRAM_USER_ID` — authorizes bot commands
- `LANGFUSE_*` — optional
- `WEBHOOK_*` — Railway prod

Do not commit secrets.

## Workflow

- **GitHub Actions:** cron twice a day (both runs are the brief); `workflow_dispatch`; `curl POST /cron/digest`
- **Railway:** `python bot.py`; Serverless; `GET /health`
- **News debugging:** `python scripts/openrouter_call.py --topic ai --period week`

## Refactoring and improvements

Agents **proactively notice** chances to improve the system and **briefly propose** them — they do not wait for an explicit request.

**Watch for:** reliability, timeouts, consistency with this file, extra LLM calls, OpenRouter cost logging.

**Boundaries:** stateless, no database, no over-engineering.

## What not to do

- Database, Redis, queues
- NewsAPI unless explicitly requested
- Over-engineering: DI, factories for fetchers
- Docs beyond what the user asked for
- A large refactor without agreement
