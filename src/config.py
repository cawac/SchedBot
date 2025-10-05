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

POSTGRES_DB = getenv("SQL_DB", "database")
POSTGRES_USER = getenv("SQL_USER", "postgres")
POSTGRES_PASSWORD = getenv("SQL_PASSWORD", "pass")
POSTGRES_HOST = getenv("SQL_HOST", "localhost")
POSTGRES_PORT = getenv("SQL_PORT", 5432)
DATABASE_URL: Final = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
