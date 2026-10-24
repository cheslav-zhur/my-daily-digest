# Project structure

Canonical annotated tree. Other docs link here and do not copy it.

```
digest/scheduled.py      # deliver_scheduled_digest() — bot POST /cron/digest
bot.py                   # entry point → digest.telegram.bot.run_bot()
digest/
  config.py              # logging, timezone, load_local_env
  observability.py       # Langfuse init / flush
  content/
    service.py           # build_digest_delivery() — brief / weather / rates
    report.py            # Telegram HTML (brief, single-topic news)
    openrouter.py        # OpenRouter chat/completions + retry + Langfuse
    news/
      topics.py          # 11 topics, 3 groups (tech / world / politics)
      period.py          # day / week / month
      prompt.py          # SUMMARY + LINK prompt (search EN, answer RU)
      parse.py           # parsing, citations whitelist, format block
      fetch.py           # fetch_topic_news() — one topic + period
    llm.py               # Gemini (not on the hot path, kept for later)
    fetchers/            # wttr.in, CoinGecko, forex, news.py (RSS — not on the hot path)
  telegram/              # bot: commands, news hub, webhook, delivery
scripts/
  wake_digest.py         # cron: POST /cron/digest, then exit
  openrouter_call.py     # dev: OpenRouter call + Langfuse
requirements.txt
.railway/railway.ts      # bot + cron: start commands, healthcheck, schedule
```

**Sources of truth (do not restate these facts in prose):**

- **News topics and groups** — `digest/content/news/topics.py`
- **Bot commands** — `digest/telegram/handlers.py` (registration + `HELP_TEXT`)
- **Environment variables** — `.env.example`, [dev.md](dev.md), [railway.md](railway.md)
- **Cron slots** — `.railway/railway.ts`

Docs describe behavior and relationships. Concrete topic and command lists stay in code so they do not drift.
