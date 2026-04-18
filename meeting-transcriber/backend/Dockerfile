# Stage 1: Build frontend with Bun
FROM oven/bun:latest AS frontend-build
WORKDIR /app
COPY frontend/package.json frontend/bun.lock* ./
RUN bun install --frozen-lockfile || bun install
COPY frontend/ .
RUN bun run build

# Stage 2: Python backend
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install cloudflared
RUN apt-get update && apt-get install -y curl && \
    curl -L --output /usr/local/bin/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && \
    chmod +x /usr/local/bin/cloudflared && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --frozen 2>/dev/null || uv sync

# Copy backend code
COPY backend/app ./app

# Alembic migration scripts and config
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic

# Copy built frontend (client-side static assets from TanStack Start build)
COPY --from=frontend-build /app/dist/client /frontend-dist

COPY entrypoint.sh .
# Normalize line endings (Windows host may have CRLF, which breaks /bin/sh shebang)
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Port is configurable via PORT env var (default 8000)
ENV PORT=8000
EXPOSE ${PORT}

ENTRYPOINT ["./entrypoint.sh"]
