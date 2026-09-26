#!/usr/bin/env bash
set -o errexit

echo "=== 1. Building Vite React Frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== 2. Installing Python Backend Dependencies ==="
pip install -r requirements.txt

echo "=== 3. Database Initialization & Seeding ==="
# Attempt initial seed; FastAPI lifespan also performs automatic schema creation & seed on startup
PYTHONPATH=. python3 backend/app/seed.py || echo "Note: Initial seed will run on app startup."

echo "=== Build Complete! Single Unified App Ready ==="
