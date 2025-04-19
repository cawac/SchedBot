from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from handlers import start_command, help_command, set_group_command, today_command, tomorrow_command, receive_group, \
    cancel, handle_message
from config import BOT_TOKEN
import logger
import logging

logger_bot = logging.getLogger("bot")

BOT_TOKEN = BOT_TOKEN

WAITING_FOR_GROUP = 1

if __name__ == "__main__":
    logger_bot.info("Bot is started")
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set_group", set_group_command)],
        states={
            WAITING_FOR_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_group)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Commands
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("tomorrow", tomorrow_command))
    app.add_handler(CommandHandler("set_group", set_group_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    logger_bot.info("Bot polling")
    app.run_polling(poll_interval=1)
