#!/bin/bash
set -e

echo "Starting API on port $PORT..."
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001} &

echo "Starting bot..."
python -m bot.main &

echo "Both services started. Waiting..."
wait -n
