#!/bin/bash
set -e

echo "Resetting test database..."
docker exec goldleads-db psql -U goldleads -c "DROP DATABASE IF EXISTS goldleads_test;"
docker exec goldleads-db psql -U goldleads -c "CREATE DATABASE goldleads_test;"
docker exec goldleads-db psql -U goldleads -c "GRANT ALL PRIVILEGES ON DATABASE goldleads_test TO goldleads;"

echo "Running migrations on test database..."
cd backend
DATABASE_URL=postgresql+psycopg://goldleads:goldleads_dev@localhost:5432/goldleads_test uv run alembic upgrade head
cd ..

echo "Test database reset complete."
