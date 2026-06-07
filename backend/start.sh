#!/bin/bash
# Railway start script
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}