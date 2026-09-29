#!/usr/bin/env bash
set -e

echo "=== Instagram Reels Trending & Growth Velocity Engine ==="
echo "Initializing database and seeding data..."
PYTHONPATH=. python3 backend/app/seed.py

echo "Starting FastAPI server on http://0.0.0.0:8000..."
PYTHONPATH=. uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
