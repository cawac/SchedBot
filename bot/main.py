from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

#from aiogram import Bot, Dispatcher, types
#from aiogram.utils import executor

from db import DatabaseHandler
from logger import logger

BOT_TOKEN = '8110534930:AAGPUBApVJbVHXHlI8dLfdeP1xRtgeJcpEY'

database = DatabaseHandler()

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("HELLO")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("I am bot for schedule in ESDC")

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(datetime.today())
    print(database.get_lessons_for_group_on_date("23-LR-CS", datetime.today()))
    await update.message.reply_text("HELLO")

async def tomorrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # TODO: SQL query
    await update.message.reply_text("I am bot for schedule in ESDC")

async def set_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    database.add_user_to_group(update.message.from_user.id, update.message.from_user.username, "23-LR-CS")
    await update.message.reply_text(f"U added to the group {'23-LR-CS'}")


# Responses
def handle_response(text: str) -> str:
    processed = text.lower()

    if "hello" in processed:
        return "hi"

    return "default"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"User {update.message.chat.id} sent message: {message_type}: '{text}'")
    response: str = handle_response(text)
    print(f"Bot {response}")
    await update.message.reply_text(response)


if __name__ == "__main__":
    print("start")
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("tomorrow", tomorrow_command))
    app.add_handler(CommandHandler("set_group", set_group_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Database set up
    database.create_tables()
    database.set_default()
    logger.info(database.add_lesson_to_group("23-LR-CS", datetime.today(), "DesignPatterns", 1, 'L'))

    print("polling")
    app.run_polling(poll_interval=3)
