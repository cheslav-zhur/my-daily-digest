# Local development

Local runs use polling and `.env`. Production lives on Railway: [docs/railway.md](railway.md).

## Environment

```bash
cp .env.example .env
```

| Variable | Role |
|----------|------|
| `TELEGRAM_BOT_TOKEN` | Token from [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_USER_ID` | Who can run commands. Fallback: `TELEGRAM_CHAT_ID` |
| `OPENROUTER_API_KEY` | News. Default model `perplexity/sonar` |
| `OPENROUTER_NEWS_MODEL` | Optional model override |
| `OPENROUTER_HTTP_REFERER` | Referer for OpenRouter rankings |
| `OPENROUTER_APP_TITLE` | App title on OpenRouter (default: `Daily Digest Bot`) |
| `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` | Optional tracing. Empty keys disable it |
| `LANGFUSE_BASE_URL` | Default `https://cloud.langfuse.com`. No quotes in the value |
| `LOG_LEVEL` | Default `INFO` |
| `GEMINI_API_KEY` | Reserved. `digest/content/llm.py` is not on the hot path |

`WEBHOOK_URL` and `WEBHOOK_SECRET` stay empty locally. Set them and the bot switches to webhook mode.

Do not commit `.env`.

## Run the bot

```bash
pip install -r requirements.txt
python bot.py
```

## News debug

`scripts/openrouter_call.py` calls OpenRouter and flushes Langfuse when the keys are set.

```bash
python scripts/openrouter_call.py --topic ai
python scripts/openrouter_call.py --topic ai --period week
python scripts/openrouter_call.py --topic all
python scripts/openrouter_call.py --topic ai --raw
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Dev dependencies stay in `requirements-dev.txt`. Railway does not install them. Conventions: [testing.md](testing.md).

GitHub Actions runs `pytest` on every push and pull request (`.github/workflows/tests.yml`). Railway waits for that workflow before deploying: [docs/railway.md](railway.md).

## Dev container

Cursor or VS Code → **Reopen in Container**. The container is Python 3.12 on Debian bookworm. On create it installs the GitHub CLI, the Railway CLI, and `requirements-dev.txt`.

App secrets come from `.env` (`load_local_env()`). The Railway CLI token is separate:

```bash
cp .env.railway.example .env.railway
```

`.env.railway` holds `RAILWAY_TOKEN` (Railway → Project → Settings → Tokens). Docker reads that file when the container is created. Rebuild after changing it.

Railway MCP in `.cursor/mcp.json` is not a working path yet. Direct OAuth to `https://mcp.railway.com` fails while dynamic client registration is disabled. The project token is enough for CLI commands on this project. Remote MCP needs a user `railway login`.

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| News shows "data unavailable" | `OPENROUTER_API_KEY` in `.env` |
| Langfuse has no traces | Both keys set, `LANGFUSE_BASE_URL` without quotes, flush after the script |
| Bot ignores commands | `TELEGRAM_USER_ID`, and that webhook variables are empty so it stays on polling |
