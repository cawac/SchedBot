from os import getenv
from datetime import datetime
from typing import Final
from pytz import timezone, utc

tz = timezone(getenv("TZ", "Europe/Vilnius"))


def now_local() -> datetime:
    utc_now = datetime.now(utc)
    return utc_now.astimezone(tz)


BOT_TOKEN: Final = getenv("BOT_TOKEN")
BOT_USERNAME: Final = "@ESDCScheduleBot"

POSTGRES_USER = getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD", "secret_pass")
POSTGRES_HOST = getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = getenv("POSTGRES_PORT", 5432)
POSTGRES_DB = getenv("POSTGRES_DB", "app_db")
DATABASE_URL: Final = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:{POSTGRES_PORT}/{POSTGRES_DB}"
