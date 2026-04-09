#!/bin/bash
set -e

echo "=== Gold Lead Research System - Local Dev Setup ==="

# 1. Create .env from example if it doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo "[1/5] Created .env from .env.example — edit it with your secrets"
else
  echo "[1/5] .env already exists, skipping"
fi

# 2. Start Postgres
echo "[2/5] Starting PostgreSQL..."
docker compose -f docker/docker-compose.yml up -d
echo "Waiting for Postgres to be ready..."
until docker exec goldleads-db pg_isready -U goldleads > /dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL is ready."

# 3. Backend dependencies
echo "[3/5] Installing backend dependencies..."
cd backend
uv sync
cd ..

# 4. Run database migrations
echo "[4/5] Running database migrations..."
cd backend
uv run alembic upgrade head
cd ..

# 5. Frontend dependencies
echo "[5/5] Installing frontend dependencies..."
cd frontend
bun install
cd ..

echo ""
echo "=== Setup complete! ==="
echo "  Backend:  cd backend && uv run python -m src.main"
echo "  Frontend: cd frontend && bun run dev"
