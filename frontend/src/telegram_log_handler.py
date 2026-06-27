import logging
import os
import traceback
from telegram import Bot
import asyncio


class TelegramLogHandler(logging.Handler):
    def __init__(self, bot_token: str, admin_chat_id: int):
        super().__init__()
        self.bot = Bot(token=bot_token)
        self.admin_chat_id = admin_chat_id
        self.setLevel(logging.ERROR)

    def emit(self, record: logging.LogRecord):
        try:
            log_entry = self.format(record)

            message_parts = [
                f"<b>Error in {record.name}</b>",
                f"",
                f"<b>Level:</b> {record.levelname}",
                f"<b>Function:</b> {record.funcName}",
                f"<b>Line:</b> {record.lineno}",
                f"",
                f"<b>Message:</b>",
                f"<code>{record.getMessage()}</code>",
            ]

            if record.exc_info:
                message_parts.append("")
                message_parts.append("<b>Traceback:</b>")
                tb_lines = traceback.format_exception(*record.exc_info)
                tb_text = ''.join(tb_lines)
                message_parts.append(f"<pre>{tb_text[:500]}</pre>")

            message = "\n".join(message_parts)

            if len(message) > 4096:
                message = message[:4090] + "\n..."

            asyncio.create_task(
                self.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=message,
                    parse_mode='HTML'
                )
            )
        except Exception:
            self.handleError(record)
