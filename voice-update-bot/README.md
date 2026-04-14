# Slack Voice Update Bot

A FastAPI service that automatically transcribes Slack voice messages and posts formatted summaries to a destination channel.

## How It Works

1. A team member sends a voice clip in the source Slack channel
2. The bot detects the audio file and downloads it
3. **Deepgram Nova-3** transcribes the audio to text
4. An **LLM via OpenRouter** formats the transcript into a structured update (summary, key points, action items, blockers)
5. The formatted update is posted to the destination channel using Slack Block Kit

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- A Slack app with the following bot scopes:
  - `channels:history`, `channels:read` (public channels)
  - `groups:history`, `groups:read` (private channels)
  - `files:read`, `chat:write`, `users:read`
- Event subscription: `message.channels` and/or `message.groups`
- [Deepgram](https://deepgram.com/) API key
- [OpenRouter](https://openrouter.ai/) API key

### Install & Run

```bash
git clone https://github.com/kailasa-l4/slack-voice-updates.git
cd slack-voice-updates
cp .env.example .env  # fill in your keys
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Environment Variables

| Variable | Description |
|---|---|
| `SLACK_BOT_TOKEN` | Bot user OAuth token (`xoxb-...`) |
| `SLACK_SIGNING_SECRET` | Found in Slack app Basic Information |
| `SOURCE_CHANNEL_ID` | Channel to listen for voice messages |
| `DEST_CHANNEL_ID` | Channel to post formatted updates |
| `DEEPGRAM_API_KEY` | Deepgram API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `LLM_MODEL` | OpenRouter model (default: `anthropic/claude-sonnet-4`) |

### Expose to Slack

Use a tunnel to make your local server reachable:

```bash
cloudflared tunnel --url http://localhost:8000
```

Set the tunnel URL as your Slack Event Subscriptions Request URL:
```
https://<your-tunnel>.trycloudflare.com/slack/events
```

## Docker

```bash
docker build -t voice-update-bot .
docker run --env-file .env -p 8000:8000 voice-update-bot
```

## Architecture

```
Slack Event -> /slack/events -> handler.py
                                  |-> slack_client.py  (download audio)
                                  |-> transcriber.py   (Deepgram Nova-3)
                                  |-> formatter.py     (OpenRouter LLM)
                                  |-> slack_client.py  (post Block Kit message)
```
