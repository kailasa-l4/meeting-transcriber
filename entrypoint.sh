#!/bin/sh

PORT="${PORT:-8000}"

# Start cloudflared tunnel in background, capture the public URL
cloudflared tunnel --url http://localhost:$PORT --no-autoupdate 2>&1 | while read -r line; do
  echo "[cloudflared] $line"
  case "$line" in
    *trycloudflare.com*)
      URL=$(echo "$line" | grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
      if [ -n "$URL" ]; then
        echo ""
        echo "=============================================="
        echo "  TUNNEL URL: $URL"
        echo "  Open this URL on your phone to start"
        echo "=============================================="
        echo ""
      fi
      ;;
  esac
done &

# Ensure persistent data directory exists
mkdir -p /app/data

# Start the FastAPI server
cd /app
exec uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
