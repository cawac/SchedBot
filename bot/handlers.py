from datetime import timedelta

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import now_local

from db import database
import logger
import logging

logger_handlers = logging.getLogger("handlers")

WAITING_FOR_GROUP = 1


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    database.create_user(update.message.from_user.id)
    await update.message.reply_text(
        "Hello!\n"
        "Thank you, for participating in testing ESDC shedule bot!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "I am bot for schedule in ESDC.\n"
        "I have several commands:\n"
        "/start - ...\n"
        "/help - how to use me\n"
        "/set_group - attach you to the group by name\n"
        "/today - show today's schedule (won't work if you not attached to any group)\n"
        "/tomorrow - show tomorrow's schedule (won't work if you not attached to any group)\n"
        "to start using this bot you need to attach you to the group by name and that only one step what you need to do"
    )


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = database.get_user_lessons_on_date(update.message.from_user.id, now_local().date())
    if response:
        message = "Today you have these lessons:\n"
        for i, lesson in enumerate(response):
            message += f"{i + 1}. {lesson["subject_name"]} ({lesson["lesson_type"]}): {lesson["lesson_start_time"]} - {lesson["lesson_end_time"]}\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("I can't find any lessons for that day. have a good day)")


async def tomorrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = database.get_user_lessons_on_date(update.message.from_user.id, now_local().date() + timedelta(days=1))
    if response:
        message = "Tomorrow you have these lessons:\n"
        for i, lesson in enumerate(response):
            message += f"{i + 1}. {lesson["subject_name"]} ({lesson["lesson_type"]}): {lesson["lesson_start_time"]} - {lesson["lesson_end_time"]}\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("I can't find any lessons for that day. have a good day)")


async def set_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    database.create_user(update.message.from_user.id)
    groups = database.get_groups()
    groups = [group.name for group in groups]
    message = "\n".join(groups)
    await update.message.reply_text(
        "Please write your group name same as in Google Sheet table (23-LR-CS)\n"
        "Groups which shedule added:" + message)
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
    dt = now_local()
    return "current date and time:" + dt.strftime("%Y-%m-%d - %H:%M:%S")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_type: str = update.message.chat.type
    text: str = update.message.text

    logger.info(f"User {update.message.chat.id} sent message: {message_type}: '{text}'")
    response: str = handle_response(text)
    logger.info(f"Bot {response}")
    await update.message.reply_text(response)
