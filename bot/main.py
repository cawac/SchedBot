from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import BOT_TOKEN, DATABASE_URL
from db import DBManager
from logger import logger

BOT_TOKEN = BOT_TOKEN

database = DBManager(DATABASE_URL)

WAITING_FOR_GROUP = 1

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    database.create_user(update.message.from_user.id)
    await update.message.reply_text(
"""
Hello!
Thank you, for participating in testing ESDC shedule bot!
""")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
"""
I am bot for schedule in ESDC. 
I have several commands: 
/start - ...
/help - how to use me
/set_group - attach you to the group by name
/today - show today's schedule (won't work if you not attached to any group)
/tomorrow - show tomorrow's schedule (won't work if you not attached to any group)

to start using this bot you need to attach you to the group by name and that only one step what you need to do
""")

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = database.get_user_lessons_on_date(update.message.from_user.id, datetime.today())
    if response:
        message = "Today you have these lessons:\n"
        for lesson in response:
            message += f"{lesson["lesson_number"]}. {lesson["subject_name"]} ({lesson["lesson_type"]}): {lesson["lesson_start_time"]} - {lesson["lesson_end_time"]}\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("I can't find any lessons for that day. have a good day)")

async def tomorrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = database.get_user_lessons_on_date(update.message.from_user.id, datetime.today() + timedelta(days=1))
    if response:
        message = "Tomorrow you have these lessons:\n"
        for lesson in response:
            message += f"{lesson["lesson_number"]}. {lesson["subject_name"]} ({lesson["lesson_type"]}): {lesson["lesson_start_time"]} - {lesson["lesson_end_time"]}\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("I can't find any lessons for that day. have a good day)")

async def set_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please write your group name same as in Excel table")
    return WAITING_FOR_GROUP

async def receive_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name: str = update.message.text
    user_info = update.message.from_user
    reply: str = database.attach_user_to_group(user_info.id, group_name)
    await update.message.reply_text(reply)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Attaching to group cancelled")
    return ConversationHandler.END


# Responses
def handle_response(text: str) -> str:
    processed = text.lower()

    if "hello" in processed:
        return "hi"

    return "default"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_type: str = update.message.chat.type
    text: str = update.message.text

    logger.info(f"User {update.message.chat.id} sent message: {message_type}: '{text}'")
    response: str = handle_response(text)
    logger.info(f"Bot {response}")
    await update.message.reply_text(response)


if __name__ == "__main__":
    logger.info("Bot is started")
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

    logger.info("Bot polling")
    app.run_polling(poll_interval=3)
