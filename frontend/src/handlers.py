from datetime import timedelta, date as date_type
from typing import Optional, Sequence
from enum import IntEnum
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

import logging
from config import now_local
from api_client import api_client
from decorators import require_user, require_group

logger = logging.getLogger(__name__)

WAITING_FOR_GROUP = 1

class FreeRoomsStates(IntEnum):
    WAITING_FOR_BUILDING = 10
    WAITING_FOR_TYPE = 11
    WAITING_FOR_LESSON_NUMBER = 12

ADMIN_TG_ID = int(os.getenv("ADMIN_TG_ID", "0"))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception occurred: {context.error}", exc_info=context.error)

async def send_html_message(update: Update, text: str):
    await update.message.reply_text(text, parse_mode='HTML')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await api_client.get_user(update.message.from_user.id)
    if not user:
        user = await api_client.create_user(update.message.from_user.id)
        if not user:
            await send_html_message(update, "Error occurred during registration. Please try again later.")
            return

    await send_html_message(update,
        "Hello!\n"
        "I am bot for schedule in ESDC.\n"
        "To start abusing me you need to <b>set up your group using /set_group</b>\n"
        "Currently bot in <b>testing stage</b>\n"
        "Thank you, for participating in testing ESDCSchedBot!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await api_client.get_user(update.message.from_user.id)
    if user:
        is_admin = user["is_admin"]
    else:
        is_admin = False

    help_text = (
        "I am bot for schedule in ESDC.\n"
        "I have several commands:\n"
        "/help - how to use me;\n"
        "/set_group - attach you to the group by group name;\n"
        "/today - show today schedule (won't work if you not attached to any group);\n"
        "/tomorrow - show tomorrow schedule (won't work if you not attached to any group).\n"
        "/week - show this week schedule\n"
        "/two_weeks - show next two weeks schedule\n"
        "/free_rooms - find free auditoriums\n"
        "/my_stats - show your statistics for this week\n"
    )

    if is_admin or update.message.from_user.id == ADMIN_TG_ID:
        help_text += "/admin_stats - show admin statistics\n"

    await send_html_message(update, help_text)

def make_day_lessons_message(lessons: list, header: str = "", footer: str = ""):
    message: str = "\n"

    if not lessons:
        message += "<b>You haven't lessons for this day</b>"
        return message + "\n" + footer

    for i, lesson in enumerate(lessons):
        message += (f"{i + 1}. <b>{lesson['subject_name']}</b> " +
                    f"{lesson['lesson_start_time']} - " +
                    f"{lesson['lesson_end_time']}\n")
    return header + message + footer

@require_user
async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict = None) -> None:
    today_lessons = await api_client.get_lessons_by_date(update.message.from_user.id, now_local().date())

    if not today_lessons and today_lessons != []:
        await send_html_message(update, "Error occurred while fetching schedule. Please try again later.")
        return
    elif today_lessons:
        message: str = make_day_lessons_message(today_lessons, header="<b>Today</b> you have these lessons:")
        await send_html_message(update, message)
    else:
        await send_html_message(update, "<b>I can't find any lessons for that day. Have a good day :)</b>")

@require_user
async def tomorrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict = None) -> None:
    tomorrow_lessons = await api_client.get_lessons_by_date(update.message.from_user.id, now_local().date() + timedelta(days=1))

    if not tomorrow_lessons and tomorrow_lessons != []:
        await send_html_message(update, "Error occurred while fetching schedule. Please try again later.")
        return
    elif tomorrow_lessons:
        message: str = make_day_lessons_message(tomorrow_lessons, header="<b>Tomorrow</b> you have these lessons:")
        await send_html_message(update, message)
    else:
        await send_html_message(update, "<b>I can't find any lessons for that day. have a good day :)</b>")

@require_user
async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict = None) -> None:
    current_date = now_local().date()
    weekday = current_date.weekday()
    end_date = current_date + timedelta(days= 6 - weekday)
    week_lessons_raw = await api_client.get_lessons_by_period(update.message.from_user.id, current_date, end_date)

    if not week_lessons_raw and week_lessons_raw != {}:
        await send_html_message(update, "Error occurred while fetching schedule. Please try again later.")
        return

    week_lessons = {date_type.fromisoformat(k): v for k, v in week_lessons_raw.items()}

    message: str = "<b>Rest of this week</b> you have these lessons:\n"
    if week_lessons:
        temp_date = current_date
        while temp_date <= end_date:
            if temp_date in week_lessons:
                message += make_day_lessons_message(week_lessons[temp_date], header=temp_date.strftime('%Y-%m-%d') + f' <b>{temp_date.strftime("%A")[:3]}</b>', footer="\n")
            elif temp_date.weekday() <= 4:
                message += make_day_lessons_message(None, header=temp_date.strftime('%Y-%m-%d') + f' <b>{temp_date.strftime("%A")[:3]}</b>', footer="\n")
            temp_date += timedelta(days=1)

        await send_html_message(update, message)
    else:
        await send_html_message(update, "I can't find any lessons for this week.")

@require_user
async def two_week_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict = None) -> None:
    current_date = now_local().date()
    weekday = current_date.weekday()
    end_date = current_date + timedelta(days=13-weekday)
    two_week_lessons_raw = await api_client.get_lessons_by_period(update.message.from_user.id, current_date, end_date)

    if not two_week_lessons_raw and two_week_lessons_raw != {}:
        await send_html_message(update, "Error occurred while fetching schedule. Please try again later.")
        return


    two_week_lessons = {date_type.fromisoformat(k): v for k, v in two_week_lessons_raw.items()}

    message: str = "<b>Rest of this week and next week</b> you have these lessons:\n"

    if two_week_lessons:
        temp_date = current_date
        while temp_date <= end_date:
            if temp_date in two_week_lessons:
                message += make_day_lessons_message(two_week_lessons[temp_date], header=temp_date.strftime('%Y-%m-%d') + f' <b>{temp_date.strftime("%A")[:3]}</b>', footer="\n")
            elif temp_date.weekday() <= 4:
                message += make_day_lessons_message(None, header=temp_date.strftime('%Y-%m-%d') + f' <b>{temp_date.strftime("%A")[:3]}</b>', footer="\n")
            temp_date += timedelta(days=1)

        await send_html_message(update, message)
    else:
        await send_html_message(update, "<b>I can't find any lessons for this two weeks.</b>")

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
    logger.info("set_group_command called")
    try:
        user = await api_client.get_user(update.message.from_user.id)
        if not user:
            user = await api_client.create_user(update.message.from_user.id)
            if not user:
                await update.message.reply_text("Registration error. Please try again later.")
                return ConversationHandler.END

        groups = await api_client.get_groups()
        logger.info(f"Got groups: {groups}")

        if not groups:
            await update.message.reply_text("Failed to load groups list. Please try again later.")
            return ConversationHandler.END

        group_names = tuple(group["name"] for group in groups)
        logger.info(f"Group names: {group_names}")
        reply_markup = make_keyboard(group_names, 3)

        await update.message.reply_text("Choose a group:", reply_markup=reply_markup)
        return WAITING_FOR_GROUP
    except Exception as e:
        logger.error(f"Error in set_group_command: {e}", exc_info=True)
        await update.message.reply_text("Error occurred. Please try again.")
        return ConversationHandler.END

async def receive_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    query = update.callback_query
    logger.info(f"Callback waiting with")
    await query.answer()

    logger.info(f"Callback received with {query.data}")
    data = query.data
    if data == "Cancel":
        await query.edit_message_text(f"Selection of group canceled", parse_mode='HTML')
        return ConversationHandler.END

    user_info = query.from_user
    user_group = data
    result = await api_client.attach_user_to_group(user_info.id, user_group)
    if result:
        await query.edit_message_text(f"<b>Group '{user_group}' selected.</b>", parse_mode='HTML')
    else:
        await query.edit_message_text("Error attaching to group. Please try again later.", parse_mode='HTML')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("<b>Attaching to group cancelled</b>")
    return ConversationHandler.END

def handle_response(text: str) -> str:
    dt = now_local()
    return ("Sorry, today I'm not interested in conversation(\n"
            "But I can tell you my current date and time)\n"
            "Current date and time:") + dt.strftime("%Y-%m-%d - %H:%M:%S")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_type: str = update.message.chat.type
    text: str = update.message.text

    logger.info(f"User {update.message.chat.id} sent message: {message_type}: '{text}'")
    response: str = handle_response(text)
    logger.info(f"Bot {response}")
    await send_html_message(update, response)

async def free_rooms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    buildings = await api_client.get_buildings()
    if not buildings:
        await send_html_message(update, "Failed to load buildings list. Please try again later.")
        return ConversationHandler.END

    reply_markup = make_keyboard(buildings, 2)
    await update.message.reply_text("Choose a building:", reply_markup=reply_markup)
    return FreeRoomsStates.WAITING_FOR_BUILDING


async def free_rooms_building_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "Cancel":
        await query.edit_message_text("Free rooms search canceled.")
        return ConversationHandler.END

    context.user_data['free_rooms_building'] = query.data

    types = await api_client.get_auditorium_types()
    types_list = ["All Types"] + types

    reply_markup = make_keyboard(types_list, 1)
    await query.edit_message_text(
        f"Building: {query.data}\nChoose auditorium type:",
        reply_markup=reply_markup
    )
    return FreeRoomsStates.WAITING_FOR_TYPE


async def free_rooms_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "Cancel":
        await query.edit_message_text("Free rooms search canceled.")
        return ConversationHandler.END

    context.user_data['free_rooms_type'] = query.data if query.data != "All Types" else None

    lesson_numbers = ["1", "2", "3", "4", "5", "6", "7"]
    reply_markup = make_keyboard(lesson_numbers, 4)

    building = context.user_data['free_rooms_building']
    type_text = query.data if query.data != "All Types" else "All"

    await query.edit_message_text(
        f"Building: {building}\nType: {type_text}\nChoose lesson number:",
        reply_markup=reply_markup
    )
    return FreeRoomsStates.WAITING_FOR_LESSON_NUMBER


async def free_rooms_lesson_number_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "Cancel":
        await query.edit_message_text("Free rooms search canceled.")
        return ConversationHandler.END

    lesson_number = int(query.data)
    building = context.user_data.get('free_rooms_building')
    auditorium_type = context.user_data.get('free_rooms_type')

    free_auds = await api_client.get_free_auditoriums(
        lesson_number=lesson_number,
        search_date=now_local().date(),
        building=building,
        auditorium_type=auditorium_type,
        tg_id=query.from_user.id
    )

    if not free_auds:
        message = f"<b>No free auditoriums found</b>\n\n"
        message += f"Building: {building}\n"
        if auditorium_type:
            message += f"Type: {auditorium_type}\n"
        message += f"Lesson: #{lesson_number}"
    else:
        message = f"<b>Free Auditoriums (Lesson #{lesson_number})</b>\n\n"
        message += f"Building: {building}\n"
        if auditorium_type:
            message += f"Type: {auditorium_type}\n"
        message += f"\nFound {len(free_auds)} auditoriums:\n\n"

        for aud in free_auds:
            message += f"• <b>{aud['name']}</b>\n"
            message += f"  Floor: {aud['floor']}"
            if aud['capacity']:
                message += f" | Capacity: {aud['capacity']}"
            message += f"\n  Type: {aud['type']}\n\n"

    await query.edit_message_text(message, parse_mode='HTML')
    return ConversationHandler.END

@require_group
async def my_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict = None) -> None:

    stats = await api_client.get_user_stats(update.message.from_user.id)
    if stats is None:
        await send_html_message(update, "Error occurred while fetching statistics. Please try again later.")
        return

    if not stats or stats.get('total_lessons', 0) == 0:
        await send_html_message(update, "<b>Your Statistics (This Week)</b>\n\nNo lessons found for this week.")
        return

    message = "<b>Your Statistics (This Week)</b>\n\n"
    message += f"Total Lessons: {stats['total_lessons']}\n"
    message += f"├─ Lectures: {stats['lectures']}\n"
    message += f"├─ Practices: {stats['practices']}\n"
    message += f"└─ Labs: {stats['labs']}\n\n"

    if stats['workload_by_day']:
        message += "<b>Workload by Day:</b>\n"
        for date_str in sorted(stats['workload_by_day'].keys()):
            count = stats['workload_by_day'][date_str]
            date_obj = date_type.fromisoformat(date_str)
            day_name = date_obj.strftime('%A')[:3]
            message += f"  {date_str} ({day_name}): {count} lessons\n"

    await send_html_message(update, message)

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await api_client.get_user(update.message.from_user.id)

    if user:
        is_admin = user["is_admin"]
        user_id = user["id"]
    else:
        is_admin = False
        user_id = None

    if not user or (not is_admin and update.message.from_user.id != ADMIN_TG_ID):
        await send_html_message(update, "This command is only available for administrators.")
        return

    engagement = await api_client.get_engagement_stats()
    popular_commands = await api_client.get_command_stats(days=7)

    if not engagement:
        await send_html_message(update, "Error occurred while fetching statistics. Please try again later.")
        return

    message = "<b>Admin Statistics (Last 7 Days)</b>\n\n"
    message += "<b>User Engagement:</b>\n"
    message += f"DAU: {engagement.get('dau', 0)}\n"
    message += f"WAU: {engagement.get('wau', 0)}\n"
    message += f"MAU: {engagement.get('mau', 0)}\n\n"

    if popular_commands:
        message += "<b>Most Popular Commands:</b>\n"
        for i, cmd in enumerate(popular_commands[:5], 1):
            message += f"{i}. {cmd['command']}: {cmd['count']} uses\n"
    else:
        message += "<b>Most Popular Commands:</b>\nNo data available\n"

    await send_html_message(update, message)
