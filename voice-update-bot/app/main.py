import logging

from fastapi import BackgroundTasks, FastAPI, Request, Response
from slack_sdk.signature import SignatureVerifier

from app.config import get_settings
from app.handler import handle_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Update Bot")


@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    # Reject retries — we already accepted the first delivery
    if request.headers.get("X-Slack-Retry-Num"):
        return Response(status_code=200)

    body = await request.body()
    payload = await request.json()

    # URL verification challenge
    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}

    # Verify Slack signature
    settings = get_settings()
    verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    if not verifier.is_valid(body.decode(), timestamp, signature):
        logger.warning("Invalid Slack signature")
        return Response(status_code=401)

    # Dispatch event processing in background
    if payload.get("type") == "event_callback":
        background_tasks.add_task(handle_event, payload)

    return Response(status_code=200)
