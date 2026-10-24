---
title: "Brief arrives late: GitHub Actions cron replaced by Railway"
date: 2026-10-21
status: decided # Railway cron service is not up yet, see Status
tags: [cron, github-actions, railway, brief]
files:
  - .railway/railway.ts
---

# Brief arrives late: cron moved from GitHub Actions to Railway

## Symptom

The morning and evening brief arrived hours after the slot. The job itself took about 8 seconds, and `POST /cron/digest` on Railway returned in 2–11 seconds. The gap was the moment GitHub created the scheduled run.

Measurements, Da Nang time:

- Late September, slots `0 0 * * *` and `0 11 * * *` (07:00 and 18:00). Morning around 09:40–10:06, evening around 21:00–23:50.
- 6–21 October, slots `17 0 * * *` and `23 11 * * *` (07:17 and 18:23). Morning steady around 11:40–12:00, evening from 21:15 to 00:34. Every run succeeded.

Moving off `:00` did not shorten the delay. The queue has been deeper since late September.

## Diagnosis

GitHub Actions `schedule` does not promise a later retry when the queue is busy. The docs say the event can be delayed under high load, worst at the start of the hour, and a queued job can be dropped. One event is created and waits on a shared scheduler. Push and pull request runs go first. A manual `workflow_dispatch` of the same workflow starts in seconds: the runner is free, and only the scheduled trigger is slow.

Other repositories report the same pattern in 2026: delay grew from tens of minutes to several hours, including for slots that are not on `:00`.

## Decision

The schedule lives in Railway cron. Slots are in [`.railway/railway.ts`](../../.railway/railway.ts).

It is a separate service. Railway runs the start command on the crontab and waits until the process exits. If the previous run is still going, the next one is skipped. `python bot.py` does not exit, so the cron must not be attached to the bot service. The cron service starts `python main.py` (send the brief, then exit) with `restartPolicyType = "never"`.

One crontab expression cannot express 07:17 and 18:23. `0 0,11 * * *` is 07:00 and 18:00 Da Nang (UTC). Railway says it does not guarantee the exact minute: slip is a few minutes, not hours. Runs must be at least 5 minutes apart.

Railway auto-reads only a root `railway.toml` or `railway.json`, and that file applies to every service. A second toml path is rejected. Both services are declared in [`.railway/railway.ts`](../../.railway/railway.ts). `railway config apply` is what sends that file. A push does not.

A second service does not add a subscription. Two short runs a day of this app are about a cent per month and sit inside Hobby usage. It costs more only if the process fails to exit and stays up: at ~0.11 GB that is about $1.10 per month for memory.

`POST /cron/digest` on the bot stays as a manual entry. `.github/workflows/daily.yml` is no longer needed for the schedule.

## Status on 2026-10-24

The decision is made. The schedule is not live yet.

- Root `railway.toml` and `railway.cron.toml` are removed. A root file would apply the bot start command to every service in the repo.
- Service settings live in `.railway/railway.ts`. Railway does not read that file on deploy. `railway config apply` sends it. Config-as-code toml is deprecated and cannot name a second file.
- Service `cron` exists in production (Singapore, `python main.py`, `0 0,11 * * *`, restart never). It has no GitHub source and no deployment. Connect it to `cheslav-zhur/my-daily-digest` `main` after this commit is pushed. Connecting earlier deploys the old root `railway.toml` and boots a second bot.
