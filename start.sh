#!/bin/bash
set -e

PORT=${PORT:-8001}

echo "Starting API on 0.0.0.0:$PORT..."
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT &
API_PID=$!

# Wait for API to be ready (using python instead of curl)
echo "Waiting for API to be ready..."
for i in $(seq 1 30); do
  if python -c "import http.client; c=http.client.HTTPConnection('localhost',$PORT); c.request('GET','/health'); r=c.getresponse(); exit(0 if r.status==200 else 1)" 2>/dev/null; then
    echo "API is ready"
    break
  fi
  echo "Waiting... ($i)"
  sleep 1
done

echo "Starting bot..."
python -m bot.main 2>&1 &
BOT_PID=$!

echo "Both services running. PID: API=$API_PID BOT=$BOT_PID"

trap "kill $API_PID $BOT_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
