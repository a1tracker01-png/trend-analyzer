#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "=== 1. Building Vite React Frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== 2. Installing Python Backend Dependencies ==="
pip install -r requirements.txt

echo "=== 3. Seeding Initial Database Tables & 4 Categories ==="
PYTHONPATH=. python3 backend/app/seed.py

echo "=== Build Complete! Single Unified App Ready ==="
