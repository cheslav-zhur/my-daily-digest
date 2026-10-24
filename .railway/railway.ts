import { defineRailway, github, preserve, project, service } from "railway/iac";

const repo = "cheslav-zhur/my-daily-digest";
const branch = "main";
const region = "asia-southeast1-eqsg3a";
const build = { builder: "RAILPACK", buildEnvironment: "V3" } as const;
const replicas = { [region]: 1 };

export default defineRailway(() => {
  const bot = service("my-daily-digest", {
    source: github(repo, { branch, checkSuites: false }),
    build,
    start: "python bot.py",
    healthcheck: "/health",
    healthcheckTimeout: 120,
    replicas,
    deploy: { sleepApplication: true },
    env: {
      CRON_SECRET: preserve(),
      LANGFUSE_PUBLIC_KEY: preserve(),
      LANGFUSE_SECRET_KEY: preserve(),
      OPENROUTER_API_KEY: preserve(),
      TELEGRAM_BOT_TOKEN: preserve(),
      TELEGRAM_CHAT_ID: preserve(),
      TELEGRAM_USER_ID: preserve(),
      WEBHOOK_SECRET: preserve(),
    },
  });

  // No GitHub source yet. origin/main still has a root railway.toml, and a
  // deploy of that commit would start this service with python bot.py.
  const cron = service("cron", {
    build,
    start: "python main.py",
    replicas,
    deploy: {
      cronSchedule: "0 0,11 * * *",
      restartPolicyType: "NEVER",
    },
    env: {
      TELEGRAM_BOT_TOKEN: bot.env.TELEGRAM_BOT_TOKEN,
      TELEGRAM_CHAT_ID: bot.env.TELEGRAM_CHAT_ID,
      LANGFUSE_PUBLIC_KEY: bot.env.LANGFUSE_PUBLIC_KEY,
      LANGFUSE_SECRET_KEY: bot.env.LANGFUSE_SECRET_KEY,
    },
  });

  return project("my-daily-digest", {
    variables: { managed: true },
    resources: [bot, cron],
  });
});
