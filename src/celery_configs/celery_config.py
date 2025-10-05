from celery.schedules import crontab
from os import getenv

broker_url = getenv("CELERY_BROKER", "amqp://user:password@rabbitmq:5672/")
timezone = getenv("TZ", "Europe/Vilnius")
enable_utc = False

beat_schedule = {
    'run-daily-task': {
        'task': 'celery_configs.tasks.daily_task',
        'schedule': crontab(hour=0, minute=0),
    },
}
