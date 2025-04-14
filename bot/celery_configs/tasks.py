from celery_configs.celery_app import app
import logging

logger = logging.getLogger(__name__)


@app.task
def daily_task():
    logger.info("Execute daily task")
