#!/bin/sh

# Start cloudflared tunnel in background, capture the public URL
cloudflared tunnel --url http://localhost:8000 --no-autoupdate 2>&1 | while read -r line; do
  echo "[cloudflared] $line"
  # Extract and highlight the tunnel URL
  case "$line" in
    *trycloudflare.com*)
      URL=$(echo "$line" | grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
      if [ -n "$URL" ]; then
        echo ""
        echo "=============================================="
        echo "  TUNNEL URL: $URL"
        echo "  SLACK ENDPOINT: $URL/slack/events"
        echo "=============================================="
        echo ""
      fi
      ;;
  esac
done &

# Start the FastAPI server
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
