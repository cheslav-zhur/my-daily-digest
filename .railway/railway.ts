import { defineRailway, github, preserve, project, service } from "railway/iac";

const repo = "cheslav-zhur/my-daily-digest";
const branch = "main";
const region = "asia-southeast1-eqsg3a";
const build = { builder: "RAILPACK", buildEnvironment: "V3" } as const;
const replicas = { [region]: 1 };

export default defineRailway(() => {
  const bot = service("bot", {
    source: github(repo, { branch, checkSuites: true }),
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

  // Wakes the sleeping bot and exits. The bot sends the brief.
  const cron = service("cron", {
    source: github(repo, { branch, checkSuites: true }),
    build: {
      ...build,
      watchPatterns: [
        "/scripts/wake_digest.py",
        "/requirements.txt",
        "/.python-version",
      ],
    },
    start: "python scripts/wake_digest.py",
    replicas,
    deploy: {
      cronSchedule: "0 0,11 * * *",
      restartPolicyType: "NEVER",
    },
    env: {
      CRON_SECRET: bot.env.CRON_SECRET,
      BOT_PRIVATE_DOMAIN: bot.env.RAILWAY_PRIVATE_DOMAIN,
      BOT_PORT: bot.env.PORT,
    },
  });

  // The CLI reads `variables`. The published ProjectDefinition type does not declare it.
  const definition = {
    resources: [bot, cron],
    variables: { managed: true },
  };
  return project("my-daily-digest", definition);
});
