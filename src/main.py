from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, \
    CallbackQueryHandler
from handlers import start_command, help_command, set_group_command, today_command, tomorrow_command, receive_group_callback, \
    handle_message, week_command, two_week_command, error_handler
from utils.logger import logger
import logging

from config import BOT_TOKEN

logger_bot = logging.getLogger("src")

WAITING_FOR_GROUP = 1


if __name__ == "__main__":
    logger_bot.info("Bot is started")
    app = Application.builder().token(BOT_TOKEN).build()

    receive_group_callback = CallbackQueryHandler(receive_group_callback)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set_group", set_group_command)],
        states={
            WAITING_FOR_GROUP: [receive_group_callback],
        },
        fallbacks=[],
        per_message=True
    )

    # Commands
    app.add_handler(receive_group_callback)

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("tomorrow", tomorrow_command))
    app.add_handler(CommandHandler("set_group", set_group_command))
    app.add_handler(CommandHandler("week", week_command))
    app.add_handler(CommandHandler("two_weeks", two_week_command))
    app.add_error_handler(error_handler)

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    logger_bot.info("Bot polling")
    app.run_polling(poll_interval=1)