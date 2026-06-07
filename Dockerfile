FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8001

CMD python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}
