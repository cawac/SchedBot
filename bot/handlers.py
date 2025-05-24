import datetime
import logging
from datetime import timedelta

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

import logger
from config import now_local
from db import database

logger_handlers = logging.getLogger("handlers")

WAITING_FOR_GROUP = 1


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    database.create_user(update.message.from_user.id)
    await update.message.reply_text(
        "Hello!\n"
        "I am bot for schedule in ESDC.\n"
        "I have several commands:\n"
        "/help - how to use me;\n"
        "/set_group - attach you to the group by group name;\n"
        "/today - show today schedule (won't work if you not attached to any group);\n"
        "/tomorrow - show tomorrow schedule (won't work if you not attached to any group).\n"
        "To start using this bot you need to set up your group using /set_group\n"
        "Thank you, for participating in testing ESDCSchedBot!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "I am bot for schedule in ESDC.\n"
        "I have several commands:\n"
        "/help - how to use me;\n"
        "/set_group - attach you to the group by group name;\n"
        "/today - show today schedule (won't work if you not attached to any group);\n"
        "/tomorrow - show tomorrow schedule (won't work if you not attached to any group).\n"
        "To start using this bot you need to set up your group using /set_group\n"
        "Thank you, for participating in testing ESDCSchedBot!"
    )


def make_day_lessons_message(lessons: list, header: str = "", footer: str = ""):
    message: str = header + "\n"

    if not lessons:
        message += "You have no lessons for this day"
        return message + "\n" + footer

    for i, lesson in enumerate(lessons):
        message += (f"{i + 1}. {lesson["subject_name"]} " +
                    f"({lesson["lesson_type"]}): " +
                    f"{lesson["lesson_start_time"]} - " +
                    f"{lesson["lesson_end_time"]}\n")
    return message + footer

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = database.get_user_lessons_on_date(update.message.from_user.id, now_local().date())
    if response:
        message: str = make_day_lessons_message(response, header="Today you have these lessons:")
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("I can't find any lessons for that day. have a good day)")


async def tomorrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = database.get_user_lessons_on_date(update.message.from_user.id, now_local().date() + timedelta(days=1))
    if response:
        message: str = make_day_lessons_message(response, header="Tomorrow you have these lessons:")
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("I can't find any lessons for that day. have a good day)")

async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_date = now_local()
    weekday = current_date.weekday()
    monday = current_date - timedelta(days=weekday)
    response = database.get_user_lessons_on_period_3(update.message.from_user.id, monday, 6)
    message: str = "This week you have these lessons:\n"
    if response:
        for date, day_lessons in response.items():
            message += make_day_lessons_message(day_lessons, header=date.strftime('%Y-%m-%d'), footer="\n")
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("I can't find any lessons for this week.")

async def two_week_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_date = now_local()
    weekday = current_date.weekday()
    monday = current_date - timedelta(days=weekday)
    response = database.get_user_lessons_on_period_3(update.message.from_user.id, monday, 13)
    message: str = "This two week you have these lessons:\n"

    if response:
        for date, day_lessons in response.items():
            message += make_day_lessons_message(day_lessons, header=date.strftime('%Y-%m-%d'), footer="\n")
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("I can't find any lessons for this two weeks.")


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
