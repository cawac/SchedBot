from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from bot import config

#from aiogram import Bot, Dispatcher, types
#from aiogram.utils import executor

from db import DatabaseHandler
from logger import logger

BOT_TOKEN = config.BOT_TOKEN

database = DatabaseHandler()

WAITING_FOR_GROUP = 1

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    response = database.get_lessons_for_user_on_date(update.message.from_user.id, datetime.today())
    if response:
        await update.message.reply_text("".join((str(item) for item in response)))
    else:
        await update.message.reply_text("I can't find any lessons for that day. have a good day)")

async def tomorrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = database.get_lessons_for_user_on_date(update.message.from_user.id, datetime.today() + timedelta(days=1))
    if response:
        await update.message.reply_text("".join((str(item) for item in response)))
    else:
        await update.message.reply_text("I can't find any lessons for that day. have a good day)")

async def set_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please write your group name same as in Excel table")
    return WAITING_FOR_GROUP
    #database.add_user_to_group(update.message.from_user.id, update.message.from_user.username, "23-LR-CS")
    #await update.message.reply_text(f"You added to the group {'23-LR-CS'}")

async def receive_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.message.text
    user_info = update.message.from_user
    res = database.attach_user_to_group(user_info.id, user_info.username, group_name)
    if res:
        await update.message.reply_text(f"You attached to group {group_name}")
    else:
        await update.message.reply_text("Something went wrong (maybe your group doesn't exist or you write group with mistakes)")
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

    print(f"User {update.message.chat.id} sent message: {message_type}: '{text}'")
    response: str = handle_response(text)
    print(f"Bot {response}")
    await update.message.reply_text(response)


if __name__ == "__main__":
    print("start")
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

    # Database set up
    database.create_tables()
    database.set_default()
    database.add_group("23-LR-CS")
    database.add_group("23-LR-JA")
    database.add_group("23-LR-JS")
    database.add_practice_to_group("23-LR-CS", datetime.today(), "ProbTheory&Stats", 6)
    database.add_practice_to_group("23-LR-JA", datetime.today(), "ProbTheory&Stats", 6)
    database.add_practice_to_group("23-LR-JS", datetime.today(), "ProbTheory&Stats", 6)
    database.add_lecture(["23-LR-CS", "23-LR-JA", "23-LR-JS"], datetime.today() + timedelta(days=1), "ProbTheory&Stats", 6)
    database.add_practice_to_group("23-LR-JA", datetime.today() + timedelta(days=1), "Algorithms and DS", 7)
    database.add_practice_to_group("23-LR-JS", datetime.today() + timedelta(days=1), "Algorithms and DS", 7)
    # logger.info(database.add_lesson_to_group("23-LR-CS", datetime.today(), "DesignPatterns", 1, 'L'))

    print("polling")
    app.run_polling(poll_interval=3)
