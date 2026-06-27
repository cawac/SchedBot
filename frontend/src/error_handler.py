import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def handle_api_errors(user_message: str = "An error occurred. Please try again later."):
    """
    Decorator to handle API errors and send user-friendly messages.

    Args:
        user_message: Message to send to user when error occurs
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            try:
                return await func(update, context, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)

                if update.message:
                    await update.message.reply_text(user_message, parse_mode='HTML')
                elif update.callback_query:
                    await update.callback_query.answer()
                    await update.callback_query.edit_message_text(user_message, parse_mode='HTML')

                return None

        return wrapper
    return decorator
