# Daily Digest Bot Setup

Step-by-step guide: local run, secrets, Railway, OpenRouter, Langfuse.

## 1. Environment variables

Copy the template and fill in values:

```bash
cp .env.example .env
```

### Required

| Variable | Where | Description |
|----------|-------|-------------|
| `TELEGRAM_BOT_TOKEN` | everywhere | Token from [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Railway / `main.py` | Chat ID for scheduled digest delivery |
| `OPENROUTER_API_KEY` | news | [OpenRouter](https://openrouter.ai/keys) key; default model `perplexity/sonar` |

### Bot (Railway / local)

| Variable | Description |
|----------|-------------|
| `TELEGRAM_USER_ID` | Who can run commands (`/brief`, `/news`, …). Fallback: `TELEGRAM_CHAT_ID` |
| `WEBHOOK_URL` + `WEBHOOK_SECRET` | Railway prod (webhook). Leave unset locally → polling |
| `RAILWAY_PUBLIC_DOMAIN` | Alternative to `WEBHOOK_URL` (set automatically on Railway) |

### Optional

| Variable | Description |
|----------|-------------|
| `OPENROUTER_NEWS_MODEL` | News model (default: `perplexity/sonar`) |
| `OPENROUTER_HTTP_REFERER` | Referer for OpenRouter (rankings on openrouter.ai) |
| `OPENROUTER_APP_TITLE` | App title in OpenRouter (default: `Daily Digest Bot`) |
| `LOG_LEVEL` | Logging level (default: `INFO`) |
| `WEBHOOK_PATH` | Telegram webhook path (default: `telegram`) |
| `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` | [Langfuse Cloud](https://cloud.langfuse.com) — OpenRouter tracing |
| `LANGFUSE_BASE_URL` | Default: `https://cloud.langfuse.com` (no quotes in value) |
| `GEMINI_API_KEY` | Reserved; **not used** in hot path (`digest/content/llm.py`) |
| `RAILWAY_TOKEN` | Dev container only: `.env.railway` — Railway CLI (`railway link`, `railway variable set`) |
| `CRON_SECRET` | Shared secret for `POST /cron/digest` (GitHub Actions + Railway) |

Do not commit `.env` to git.

## 2. Local run

```bash
pip install -r requirements.txt
```

**Scheduled digest (same as cron):**

```bash
python main.py
```

**Telegram bot (commands):**

```bash
python bot.py
```

Without `WEBHOOK_URL` / `WEBHOOK_SECRET`, the bot runs in **polling** mode.

### News debug (OpenRouter + Langfuse)

```bash
python scripts/openrouter_call.py --topic ai      # one topic
python scripts/openrouter_call.py --topic all     # all topics (11)
python scripts/openrouter_call.py --topic ai --raw  # raw API JSON
```

The script calls `init_observability()` and `flush_observability()` — traces appear in Langfuse when keys are set.

## 3. Secrets (CLI)

**Railway** (bot + digest):

```bash
railway variable set TELEGRAM_BOT_TOKEN=... OPENROUTER_API_KEY=... CRON_SECRET=...
```

Full Railway variable list: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_USER_ID`, `OPENROUTER_API_KEY`, `LANGFUSE_*`, `WEBHOOK_*`, `CRON_SECRET`

## 4. Scheduled brief

The cron service runs `python main.py` and exits. The schedule is `0 0,11 * * *` (07:00 and 18:00 Asia/Ho_Chi_Minh).

Both services are declared in [`.railway/railway.ts`](.railway/railway.ts). `railway config apply` is what puts that file on Railway. A push to `main` deploys code for a service that has a GitHub source. It does not apply the file, and it does not copy one service's start command onto the other.

The cron service needs `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (same values as the bot).

## 5. Railway (bot)

Declared in [`.railway/railway.ts`](.railway/railway.ts). On the service:

- **Start command:** `python bot.py`
- **Healthcheck:** `GET /health`
- Enable **Serverless** in the Railway UI
- Set variables (see §3)

Webhook mode: `WEBHOOK_URL` or `RAILWAY_PUBLIC_DOMAIN` + `WEBHOOK_SECRET`.

Cron endpoint: `POST /cron/digest` with `Authorization: Bearer <CRON_SECRET>`. Always brief-only; news is on-demand via the bot hub.

## 6. Langfuse

If keys are empty, tracing is disabled (`LANGFUSE_TRACING_ENABLED=false`).

News traces:

- `openrouter-news` — per-topic on-demand requests (topic + period)
- `openrouter-chat` — low-level API call

Common mistake: extra quotes in `.env`:

```bash
# bad
LANGFUSE_BASE_URL="https://cloud.langfuse.com"

# good
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

The code also strips quotes in `digest/observability.py`.

## 7. Dev container

VS Code / Cursor → **Reopen in Container**.

- Python 3.12 (Debian bookworm), GitHub CLI, Railway CLI, `pip install` on create
- App secrets: `.env` (read by `load_local_env()` from the mounted workspace)
- Railway CLI: `cp .env.railway.example .env.railway` — only `RAILWAY_TOKEN` is injected into the container (Docker reads that file when the container is created; rebuild after changing it)
- Railway MCP (`.cursor/mcp.json`): status of this work is unclear for now. Direct OAuth to `https://mcp.railway.com` fails while dynamic client registration is disabled. The project token is enough for CLI commands on this project; remote MCP needs a user `railway login`, which is not set up. Do not treat MCP as a working path until that is settled.

## 8. Bot commands

| Command | Description |
|---------|-------------|
| `/brief` | Date, weather, rates, motivation |
| `/news` | News hub: pick topic → day/week/month |
| `/weather` | Da Nang weather |
| `/rates` | BTC, ETH, VND/USD |
| `/help` | Help |

Access restricted to `TELEGRAM_USER_ID`.

## Troubleshooting

| Issue | What to check |
|-------|---------------|
| News shows "data unavailable" | `OPENROUTER_API_KEY` in `.env` / Railway |
| Langfuse not recording traces | keys, `LANGFUSE_BASE_URL` without quotes, `flush` after request |
| Bot not responding | `TELEGRAM_USER_ID`, polling vs webhook, Railway logs |
| Empty cron | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` on the cron service; Railway cron logs |

For news architecture details, see [`AGENTS.md`](AGENTS.md).
