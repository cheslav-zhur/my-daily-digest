# AGENTS.md

## Project

**Daily Digest Bot** — a personal morning briefing in Telegram.

A Railway cron service runs **twice a day** (slots in [`.railway/railway.ts`](.railway/railway.ts)). It `POST`s `/cron/digest` and exits. The bot wakes and sends the brief:

- Weather in Da Nang
- Rates: BTC, ETH, VND/USD
- Motivation

News is **not** sent by cron: only on request through the «Новости» hub (button under the brief, or `/news`) — topic → period → one LLM call.

**Stack:** Python 3.12, GitHub Actions (tests), Railway (webhook bot that sleeps when idle, plus cron), OpenRouter (`perplexity/sonar`), Langfuse (optional), Telegram Bot API, wttr.in, CoinGecko.

**No database** — every run is stateless.

**Local run:** [`docs/dev.md`](docs/dev.md). **Railway:** [`docs/railway.md`](docs/railway.md). **Layout:** [`docs/structure.md`](docs/structure.md).

## GitHub

- **Repo:** https://github.com/cheslav-zhur/my-daily-digest

## Run modes

| Mode | Entry point | Where it runs |
|------|-------------|---------------|
| Morning and evening: brief only (+ «Новости» button) | `python scripts/wake_digest.py` → `POST /cron/digest` | Railway cron wakes the bot |
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

Perplexity ended Sonar Chat Completions support on 2026-09-27 and points `sonar` at the Agent API preset `fast` (`POST /v1/agent`). Sync calls still answer. Stay on OpenRouter `perplexity/sonar` until `citations`, `search_results`, or `search_recency_filter` break. `fast` is not an OpenRouter model id: the filter moves under `web_search.filters`, and the reply is an `output` array, so `parse.py` would not read it. Do not move news to Gemini to spend GCP credits.

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

Conventions and how to run: see [`docs/testing.md`](docs/testing.md). In short: `pytest`, tests in `tests/`, dev dependencies in `requirements-dev.txt` (not in prod).

## Code rules

1. **Graceful degradation** — each fetch in its own `try/except`; one failed news topic does not take down the hub
2. **Telegram HTML** — only `<b>` and `<a href>` in news; `parse_mode=HTML`
3. **VND/USD** — a separate forex API, not CoinGecko
4. **News** — plain text from the model; HTML is assembled in `report.py`
5. **Citations** — URL whitelist from `citations`, `search_results`, `message.annotations` (OpenRouter)

## Secrets

See [`docs/railway.md`](docs/railway.md) and [`docs/dev.md`](docs/dev.md). In short:

- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `OPENROUTER_API_KEY` — required on Railway
- `CRON_SECRET` — Railway, `Authorization: Bearer` for `POST /cron/digest`
- `TELEGRAM_USER_ID` — authorizes bot commands
- `LANGFUSE_*` — optional
- `WEBHOOK_*` — Railway prod

Do not commit secrets.

## Workflow

- **Railway cron:** `python scripts/wake_digest.py` twice a day; the bot sends the brief. Schedule in `.railway/railway.ts`
- **Railway bot:** `python bot.py`; sleeps when idle (`sleepApplication`); `GET /health`
- **Settings in `.railway/railway.ts`:** `railway config apply`. A push deploys code after tests pass and does not apply that file. Details in [`docs/railway.md`](docs/railway.md)
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
