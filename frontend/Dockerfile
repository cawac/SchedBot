FROM python:3.12-slim-bullseye

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPATH=/app/src

RUN apt-get update \
  && apt-get install -y netcat \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src

CMD ["sh", "-c", "echo 'Waiting for backend...' && while ! nc -z backend 8000; do sleep 1; done && echo 'Backend ready!' && cd /app/src && python3 main.py"]
