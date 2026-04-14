FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install cloudflared
ADD https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 /usr/local/bin/cloudflared
RUN chmod +x /usr/local/bin/cloudflared

WORKDIR /app

# Install Python dependencies
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --frozen || uv sync

# Copy backend code
COPY backend/app ./app

# Copy frontend (served as static files)
COPY frontend /frontend

# Copy entrypoint
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
