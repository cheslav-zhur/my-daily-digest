# Daily Digest Bot

[![Python](https://img.shields.io/badge/python-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-LLM-6B21A8)](https://openrouter.ai)
[![Langfuse](https://img.shields.io/badge/Langfuse-tracing-F04438)](https://langfuse.com)

[![Tests](https://img.shields.io/github/actions/workflow/status/cheslav-zhur/my-daily-digest/tests.yml?branch=main&label=tests)](https://github.com/cheslav-zhur/my-daily-digest/actions/workflows/tests.yml)
[![Railway](https://img.shields.io/badge/Railway-deploy-0B0D0E?logo=railway&logoColor=white)](https://railway.app)

Personal morning briefing in Telegram: weather, crypto/forex rates, and news (11 topics across tech, world, politics).

Stateless — no database, each run is independent.

## What it sends

- **Weather** — Da Nang (wttr.in)
- **Rates** — BTC, ETH (CoinGecko), VND/USD (forex API)
- **News** — 11 topics in 3 groups (tech, world, politics) via [OpenRouter](https://openrouter.ai) (`perplexity/sonar`): Russian summary + links; search in English

Full digest HTML is assembled in code (`report.py`) — no LLM for weather/rates layout.

## Stack

- Python 3.12
- **Railway** — cron wakes the bot (`POST /cron/digest`); the bot sends the brief (`bot.py`, webhook)
- **OpenRouter** — news (Perplexity Sonar)
- **Langfuse** — optional tracing
- python-telegram-bot, requests, feedparser

## Architecture

```mermaid
flowchart LR
  subgraph triggers [Triggers]
    CronSvc[Railway cron<br/>twice a day]
    User[Telegram user<br/>/brief · /news]
  end

  subgraph railway [Railway · bot.py]
    Cron["POST /cron/digest"]
    Bot[Bot handlers]
    Brief[Brief builder<br/>weather · rates · motivation]
    News[News hub<br/>topic → period]
    OR[OpenRouter<br/>perplexity/sonar]
  end

  subgraph sources [External APIs]
    Wttr[wttr.in]
    CG[CoinGecko]
    FX[Forex API]
  end

  TG[Telegram chat]
  LF[Langfuse<br/>optional]

  CronSvc --> Cron
  User --> Bot
  Cron --> Brief
  Bot -->|/brief| Brief
  Bot -->|/news or button| News
  Brief --> Wttr & CG & FX
  Brief -->|1 message + News button| TG
  News --> OR
  OR -.->|trace| LF
  OR -->|1 topic message| TG
```

Brief on cron does **not** call the LLM. News run only on demand: one OpenRouter request per topic + period.

## Quick start

```bash
cp .env.example .env   # fill TELEGRAM_* and OPENROUTER_API_KEY
pip install -r requirements.txt
python bot.py          # bot (polling locally); /brief sends one brief
```

**Docs:** [local development](docs/dev.md), [Railway](docs/railway.md), [layout](docs/structure.md), [tests](docs/testing.md).

## Modes

| Mode | Entry | Where |
|------|-------|-------|
| Scheduled digest | `python scripts/wake_digest.py` | Railway cron wakes the bot |
| Bot commands | `python bot.py` | Railway or local |

Agent / contributor notes: **[AGENTS.md](AGENTS.md)**.
