from datetime import timedelta
from typing import Optional, Sequence

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

import logging
from config import now_local
from db import database_manager

logger_handlers = logging.getLogger("handlers")

WAITING_FOR_GROUP = 1


async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    logger_handlers.error(f"Exception occurred: {context.error}")

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    database_manager.create_user(tg_id=update.message.from_user.id)
    await update.message.reply_text(
        "Hello!\n"
        "I am src for schedule in ESDC.\n"
        "To start abusing me you need to set up your group using /set_group\n"
        "Currently src in testing stage \n"
        "Thank you, for participating in testing ESDCSchedBot!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "I am src for schedule in ESDC.\n"
        "I have several commands:\n"
        "/help - how to use me;\n"
        "/set_group - attach you to the group by group name;\n"
        "/today - show today schedule (won't work if you not attached to any group);\n"
        "/tomorrow - show tomorrow schedule (won't work if you not attached to any group).\n"
        "/week - in development\n"
        "/two_weeks - in development"
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
    response = database_manager.get_user_lessons_on_date(update.message.from_user.id, now_local().date())
    if response:
        message: str = make_day_lessons_message(response, header="Today you have these lessons:")
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("I can't find any lessons for that day. have a good day)")


async def tomorrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = database_manager.get_user_lessons_on_date(update.message.from_user.id, now_local().date() + timedelta(days=1))
    if response:
        message: str = make_day_lessons_message(response, header="Tomorrow you have these lessons:")
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("I can't find any lessons for that day. have a good day)")

async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_date = now_local()
    weekday = current_date.weekday()
    monday = current_date - timedelta(days=weekday)
    response = database_manager.get_user_lessons_on_period_3(update.message.from_user.id, monday, 6)
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
    response = database_manager.get_user_lessons_on_period_3(update.message.from_user.id, monday, 13)
    message: str = "This two week you have these lessons:\n"

    if response:
        for date, day_lessons in response.items():
            message += make_day_lessons_message(day_lessons, header=date.strftime('%Y-%m-%d'), footer="\n")
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("I can't find any lessons for this two weeks.")

def make_keyboard(data: Sequence[str], columns: int = 1) -> InlineKeyboardMarkup:
    if columns < 1 or columns > 5:
        columns = 1

    keyboard = []

    for index in range(0, len(data), columns):
        buttons_in_row = [InlineKeyboardButton(data[index_new], callback_data=data[index_new]) for index_new in range(index, min(index + columns, len(data)))]
        keyboard.append(buttons_in_row)

    keyboard.append([InlineKeyboardButton("Cancel", callback_data="Cancel")])
    return InlineKeyboardMarkup(keyboard)


async def set_group_command(update, context: ContextTypes.DEFAULT_TYPE) -> int:
    database_manager.create_user(tg_id=update.message.from_user.id)
    groups = database_manager.get_groups()
    group_names = tuple(group.name for group in groups)
    reply_markup = make_keyboard(group_names, 3)

    await update.message.reply_text("Choose a group:", reply_markup=reply_markup)
    return WAITING_FOR_GROUP


async def receive_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    query = update.callback_query
    logger_handlers.info(f"Callback waiting with")
    await query.answer()

    logger_handlers.info(f"Callback received with {query.data}")
    data = query.data
    if data == "Cancel":
        await query.edit_message_text(f"Selection of group canceled")
        return ConversationHandler.END

    user_info = query.from_user
    user_group = data
    database_manager.attach_user_to_group(user_info.id, user_group)
    await query.edit_message_text(f"Group '{user_group}' selected.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Attaching to group cancelled")
    return ConversationHandler.END


# Responses
def handle_response(text: str) -> str:
    dt = now_local()
    return ("Sorry, today I'm not interested in conversation(\n"
            "But I can tell you my current date and time)\n"
            "Current date and time:") + dt.strftime("%Y-%m-%d - %H:%M:%S")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_type: str = update.message.chat.type
    text: str = update.message.text

    logger_handlers.info(f"User {update.message.chat.id} sent message: {message_type}: '{text}'")
    response: str = handle_response(text)
    logger_handlers.info(f"Bot {response}")
    await update.message.reply_text(response)
