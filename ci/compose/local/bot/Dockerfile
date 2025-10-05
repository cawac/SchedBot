FROM python:3.12-slim-bullseye

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPATH=/bot

RUN apt-get update \
  && apt-get install -y build-essential \
  && apt-get install -y libpq-dev \
  && apt-get install -y gettext \
  && apt-get install -y git procps \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*


COPY ./src/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
RUN pip install --no-cache-dir psycopg2-binary

COPY ./compose/local/src/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/src/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

# COPY ./compose/local/bot/celery/worker/start /start-celeryworker
# RUN sed -i 's/\r$//g' /start-celeryworker
# RUN chmod +x /start-celeryworker
#
# COPY ./compose/local/bot/celery/beat/start /start-celerybeat
# RUN sed -i 's/\r$//g' /start-celerybeat
# RUN chmod +x /start-celerybeat
#
# COPY ./compose/local/bot/celery/flower/start /start-flower
# RUN sed -i 's/\r$//g' /start-flower
# RUN chmod +x /start-flower

WORKDIR /bot

EXPOSE 8000

# ENTRYPOINT ["/entrypoint"]