import logging
from datetime import datetime
import pytz
from config import tz


class LocalTimezoneFormatter(logging.Formatter):
    def converter(self, timestamp):
        utc_dt = datetime.fromtimestamp(timestamp, tz=pytz.utc)
        return utc_dt.astimezone(tz)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        return dt.strftime("%Y-%m-%d - %H:%M:%S")

formatter = LocalTimezoneFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

file_handler = logging.FileHandler("bot.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("Logger initialized")
