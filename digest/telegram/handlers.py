from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime

from telegram import BotCommand, Message, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from digest.config import DA_NANG_TZ
from digest.content.news.fetch import fetch_topic_news
from digest.content.report import build_single_topic_news_html
from digest.content.service import DigestSection, build_digest_delivery
from digest.content.telegram_html import html_to_plain_text
from digest.observability import flush_observability
from digest.telegram.news_hub import (
    HUB_INTRO_HTML,
    PERIOD_PROMPT_HTML,
    decode_callback,
    period_keyboard,
    topic_keyboard,
)
from digest.content.news.topics import TOPIC_BY_ID

HELP_TEXT = (
    "<b>Daily Digest Bot</b>\n\n"
    "Команды:\n"
    "/brief — дата, погода, курсы, мотивация\n"
    "/weather — погода в Da Nang\n"
    "/rates — курсы BTC, ETH и VND/USD\n"
    "/news — новости: тема → период\n"
    "/help — эта справка"
)

BOT_COMMANDS = [
    BotCommand("start", "Справка по командам"),
    BotCommand("help", "Справка по командам"),
    BotCommand("brief", "Бриф: погода, курсы, мотивация"),
    BotCommand("weather", "Погода в Da Nang"),
    BotCommand("rates", "Курсы BTC, ETH, VND/USD"),
    BotCommand("news", "Новости: тема и период"),
]

UNAUTHORIZED_TEXT = "Это личный бот. Доступ только у владельца."
LOADING_TEXT = "⏳ Собираю данные..."


def authorized_user_id() -> str:
    user_id = os.environ.get("TELEGRAM_USER_ID", "").strip()
    if user_id:
        return user_id
    return os.environ.get("TELEGRAM_CHAT_ID", "").strip()


def is_authorized(update: Update) -> bool:
    user = update.effective_user
    if user is None:
        return False
    allowed = authorized_user_id()
    return bool(allowed) and str(user.id) == allowed


async def reply_unauthorized(update: Update) -> None:
    if update.message:
        await update.message.reply_text(UNAUTHORIZED_TEXT)


async def edit_html_message(
    message: Message,
    html_text: str,
    *,
    reply_markup=None,
) -> None:
    try:
        await message.edit_text(
            html_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )
    except Exception:
        logging.exception(
            "Telegram edit failed with parse_mode=HTML, retrying as plain text"
        )
        await message.edit_text(
            html_to_plain_text(html_text),
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )


async def send_html_reply(
    message: Message,
    html_text: str,
    *,
    reply_markup=None,
) -> None:
    try:
        await message.reply_html(
            html_text,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )
    except Exception:
        logging.exception(
            "Telegram reply failed with parse_mode=HTML, retrying as plain text"
        )
        await message.reply_text(
            html_to_plain_text(html_text),
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )


async def deliver_section(status: Message, section: DigestSection) -> None:
    try:
        delivery = await asyncio.to_thread(build_digest_delivery, section)
        if not delivery.messages:
            await status.edit_text("Данные недоступны.")
        else:
            await edit_html_message(status, delivery.messages[0])
    except Exception:
        logging.exception("section %s failed", section.value)
        await status.edit_text("Ошибка при сборе данных.")


async def run_section(update: Update, section: DigestSection) -> None:
    if update.message is None:
        return

    if not is_authorized(update):
        await reply_unauthorized(update)
        return

    status = await update.message.reply_text(LOADING_TEXT)
    await deliver_section(status, section)


async def open_news_hub_message(message: Message) -> None:
    await message.reply_html(
        HUB_INTRO_HTML,
        reply_markup=topic_keyboard(),
        disable_web_page_preview=True,
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        await reply_unauthorized(update)
        return
    if update.message:
        await update.message.reply_html(HELP_TEXT, disable_web_page_preview=True)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def cmd_brief(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_section(update, DigestSection.BRIEF)


async def cmd_weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_section(update, DigestSection.WEATHER)


async def cmd_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_section(update, DigestSection.RATES)


async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    if not is_authorized(update):
        await reply_unauthorized(update)
        return
    await open_news_hub_message(update.message)


async def on_news_hub_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if query is None:
        return

    if not is_authorized(update):
        await query.answer(UNAUTHORIZED_TEXT, show_alert=True)
        return

    decoded = decode_callback(query.data or "")
    if decoded is None:
        await query.answer()
        return

    action, topic_id, period = decoded
    await query.answer()

    message = query.message
    if message is None or not isinstance(message, Message):
        return

    if action == "open":
        await edit_html_message(
            message, HUB_INTRO_HTML, reply_markup=topic_keyboard()
        )
        return

    if action == "topic" and topic_id is not None:
        topic = TOPIC_BY_ID[topic_id]
        prompt = PERIOD_PROMPT_HTML.format(topic=topic.label.rstrip(":"))
        await edit_html_message(
            message, prompt, reply_markup=period_keyboard(topic_id)
        )
        return

    if action == "period" and topic_id is not None and period is not None:
        await message.edit_text(LOADING_TEXT)
        report_date = datetime.now(DA_NANG_TZ).strftime("%Y-%m-%d")
        try:
            result = await asyncio.to_thread(
                fetch_topic_news, topic_id, report_date, period
            )
            html = build_single_topic_news_html(
                report_date,
                result.topic,
                result.text,
                period=result.period,
                cost=result.cost,
                failure_reason=result.failure_reason,
            )
            await edit_html_message(
                message, html, reply_markup=topic_keyboard()
            )
            await asyncio.to_thread(flush_observability)
        except Exception:
            logging.exception("news hub fetch failed for %s/%s", topic_id, period)
            await edit_html_message(
                message,
                "Ошибка при сборе данных.",
                reply_markup=topic_keyboard(),
            )


async def on_unauthorized_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if is_authorized(update):
        return
    await reply_unauthorized(update)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(BOT_COMMANDS)


def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("brief", cmd_brief))
    application.add_handler(CommandHandler("weather", cmd_weather))
    application.add_handler(CommandHandler("rates", cmd_rates))
    application.add_handler(CommandHandler("news", cmd_news))
    application.add_handler(
        CallbackQueryHandler(on_news_hub_callback, pattern=r"^nh:")
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, on_unauthorized_message)
    )
