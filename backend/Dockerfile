FROM python:3.12-slim-bullseye

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPATH=/app/src

RUN apt-get update \
  && apt-get install -y build-essential \
  && apt-get install -y libpq-dev \
  && apt-get install -y curl \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src

EXPOSE 8000

CMD ["sh", "-c", "cd /app/src && python3 -m alembic upgrade head && python3 load_csv_to_oltp.py || true && uvicorn api:app --host 0.0.0.0 --port 8000 --reload"]
