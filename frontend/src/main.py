import os
import logging
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, \
    CallbackQueryHandler, Application
from handlers import (
    start_command, help_command, set_group_command, today_command, tomorrow_command,
    receive_group_callback, handle_message, week_command, two_week_command, error_handler,
    free_rooms_command, free_rooms_building_selected, free_rooms_type_selected,
    free_rooms_lesson_number_selected, my_stats_command, admin_stats_command,
    FreeRoomsStates
)

from config import BOT_TOKEN
from telegram_log_handler import TelegramLogHandler

logger_bot = logging.getLogger(__name__)

ADMIN_TG_ID = int(os.getenv("ADMIN_TG_ID", "0"))

if ADMIN_TG_ID:
    telegram_handler = TelegramLogHandler(BOT_TOKEN, ADMIN_TG_ID)
    logging.getLogger().addHandler(telegram_handler)

WAITING_FOR_GROUP = 1

WEBHOOK_MODE = os.getenv("WEBHOOK_MODE", "false").lower() == "true"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8443"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")


if __name__ == "__main__":
    logger_bot.info("Bot is starting")
    app = Application.builder().token(BOT_TOKEN).build()

    set_group_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set_group", set_group_command)],
        states={
            WAITING_FOR_GROUP: [CallbackQueryHandler(receive_group_callback)],
        },
        fallbacks=[]
    )

    free_rooms_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("free_rooms", free_rooms_command)],
        states={
            FreeRoomsStates.WAITING_FOR_BUILDING: [CallbackQueryHandler(free_rooms_building_selected)],
            FreeRoomsStates.WAITING_FOR_TYPE: [CallbackQueryHandler(free_rooms_type_selected)],
            FreeRoomsStates.WAITING_FOR_LESSON_NUMBER: [CallbackQueryHandler(free_rooms_lesson_number_selected)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(set_group_conv_handler)
    app.add_handler(free_rooms_conv_handler)
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("tomorrow", tomorrow_command))
    app.add_handler(CommandHandler("week", week_command))
    app.add_handler(CommandHandler("two_weeks", two_week_command))
    app.add_handler(CommandHandler("my_stats", my_stats_command))
    app.add_handler(CommandHandler("admin_stats", admin_stats_command))
    app.add_error_handler(error_handler)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if WEBHOOK_MODE:
        logger_bot.info(f"Starting bot in webhook mode on port {WEBHOOK_PORT}")
        logger_bot.info(f"Webhook URL: {WEBHOOK_URL}{WEBHOOK_PATH}")
        app.run_webhook(
            listen="0.0.0.0",
            port=WEBHOOK_PORT,
            url_path=WEBHOOK_PATH,
            webhook_url=f"{WEBHOOK_URL}{WEBHOOK_PATH}",
        )
    else:
        logger_bot.info("Starting bot in polling mode")
        app.run_polling(poll_interval=1)
