from celery import Celery

app = Celery('bot')
app.config_from_object('celery_configs.celery_config')
app.autodiscover_tasks(['celery_configs'])
