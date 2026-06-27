from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from api_client import api_client


def require_user(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = await api_client.get_user(update.message.from_user.id)
        if not user:
            await update.message.reply_text(
                "You are not registered. Use /start command",
                parse_mode='HTML'
            )
            return None
        return await func(update, context, *args, user=user, **kwargs)
    return wrapper


def require_group(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = await api_client.get_user(update.message.from_user.id)
        if not user:
            await update.message.reply_text(
                "You are not registered. Use /start command",
                parse_mode='HTML'
            )
            return None

        if not user.get("group_id"):
            await update.message.reply_text(
                "Please set your group first using /set_group",
                parse_mode='HTML'
            )
            return None

        return await func(update, context, *args, user=user, **kwargs)
    return wrapper
