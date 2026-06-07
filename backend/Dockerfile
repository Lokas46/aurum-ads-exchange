FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/alembic/versions

EXPOSE 8001

# Wait for DB then start app
CMD ["sh", "-c", "echo '=== Starting wait_for_db ===' && python wait_for_db.py && echo '=== Starting uvicorn ===' && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]