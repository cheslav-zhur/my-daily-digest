# Railway

Both services are declared in [`.railway/railway.ts`](../.railway/railway.ts). They deploy from `cheslav-zhur/my-daily-digest`, branch `main`, region `asia-southeast1-eqsg3a`.

## Push and apply

A push to `main` builds and deploys the bot. The cron service deploys only when the push touches its watch paths in `.railway/railway.ts`: `scripts/wake_digest.py`, `requirements.txt`, or `.python-version`. Both services wait for GitHub Actions first (`checkSuites`). The check is `.github/workflows/tests.yml`. A failed `pytest` run skips that deployment, and the previous image stays. Railway gives the checks two hours, then skips the deployment.

Service settings in `.railway/railway.ts` reach Railway through `railway config apply`. That covers the start command, the schedule, sleep, and the variable references. Run `railway config plan` before apply.

## Bot

Service `bot`.

- Start: `python bot.py`
- Healthcheck: `GET /health` (timeout 120s)
- Sleeps when idle: `deploy.sleepApplication` in `.railway/railway.ts`
- Webhook when `WEBHOOK_URL` is set, or when `RAILWAY_PUBLIC_DOMAIN` and `WEBHOOK_SECRET` are set
- `POST /cron/digest` with `Authorization: Bearer <CRON_SECRET>` sends the brief only. News stays on demand in the bot

`RAILWAY_PUBLIC_DOMAIN`, `PORT`, and `RAILWAY_PRIVATE_DOMAIN` are set by Railway.

## Cron

Service `cron`. It runs `python scripts/wake_digest.py`, which `POST`s `/cron/digest` on the bot over the private network, then exits. The bot wakes and sends the brief.

- Schedule: `0 0,11 * * *` in `.railway/railway.ts` (07:00 and 18:00 Asia/Ho_Chi_Minh)
- `restartPolicyType`: `NEVER`
- `CRON_SECRET`, `BOT_PRIVATE_DOMAIN`, and `BOT_PORT` are references to the bot service (`CRON_SECRET`, `RAILWAY_PRIVATE_DOMAIN`, `PORT`)
- Watch paths skip a cron deploy when those three files are unchanged

## Variables

```bash
railway variable set TELEGRAM_BOT_TOKEN=... OPENROUTER_API_KEY=... CRON_SECRET=...
```

On the bot: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_USER_ID`, `OPENROUTER_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `WEBHOOK_SECRET`, `CRON_SECRET`.

On the cron service the three references above are enough. The wake script does not send Telegram messages itself.

The CLI token for this repo is `RAILWAY_TOKEN` in `.env.railway`. See [docs/dev.md](dev.md).

## Langfuse

Empty keys disable tracing (`LANGFUSE_TRACING_ENABLED=false`).

News traces:

- `openrouter-news` — one topic and period
- `openrouter-chat` — the API call

`LANGFUSE_BASE_URL` defaults to `https://cloud.langfuse.com`. Leave quotes out of the value.

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| Push did not change the cron schedule or start command | Those fields live in `.railway/railway.ts`. Apply with `railway config apply` |
| Deploy stayed `WAITING` or became `SKIPPED` | GitHub Actions on that commit. A failed `pytest` skips the deploy |
| Brief did not arrive at 07:00 or 18:00 | Cron logs. `CRON_SECRET` matches the bot. `BOT_PRIVATE_DOMAIN` and `BOT_PORT` point at the bot |
| Bot not responding | `TELEGRAM_USER_ID`, webhook variables, bot logs |
