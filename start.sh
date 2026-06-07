#!/bin/bash
set -e

PORT=${PORT:-8001}

echo "Starting API on 0.0.0.0:$PORT..."
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT &
API_PID=$!

# Wait for API to be ready
for i in $(seq 1 30); do
  if curl -sf http://localhost:$PORT/health > /dev/null 2>&1; then
    echo "API is ready"
    break
  fi
  echo "Waiting for API... ($i)"
  sleep 1
done

echo "Starting bot..."
python -m bot.main &
BOT_PID=$!

echo "Both services running. API_PID=$API_PID BOT_PID=$BOT_PID"

# Wait for any process to exit, then kill the other
trap "kill $API_PID $BOT_PID 2>/dev/null; exit" SIGINT SIGTERM
wait $API_PID $BOT_PID
