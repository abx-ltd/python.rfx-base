import hashlib
import hmac
import time
from collections import deque
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException
from pipe import Pipe

from . import config, logger

router = APIRouter(prefix="/webhook", tags=["webhooks"])

MAX_AGE_SECONDS = 300
MAX_HISTORY = 50

_received_webhooks: deque[dict] = deque(maxlen=MAX_HISTORY)


def _verify_signature(body: bytes, timestamp: str, signature: str) -> bool:
    message = f"{timestamp}.".encode() + body
    expected = hmac.new(
        config.WEBHOOK_SECRET.encode(), message, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/rfx-discuss")
async def receive_discuss_webhook(request: Request):
    """Receive webhook callbacks from rfx-discuss domain.

    Verifies HMAC-SHA256 signature and timestamp freshness.
    """
    timestamp = request.headers.get("X-Webhook-Timestamp", "")
    signature = request.headers.get("X-Webhook-Signature", "")
    body = await request.body()

    try:
        if abs(time.time() - int(timestamp)) > MAX_AGE_SECONDS:
            raise HTTPException(status_code=403, detail="Timestamp expired")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp header")

    if not _verify_signature(body, timestamp, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()
    logger.info(
        "[Webhook-Receiver] event=%s resource=%s id=%s",
        payload.get("event"),
        payload.get("resource"),
        payload.get("identifier"),
    )

    _received_webhooks.append(
        {
            "received_at": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }
    )

    return {"status": "ok", "event": payload.get("event")}


@router.get("/rfx-discuss/health")
async def discuss_webhook_health():
    return {"status": "ok", "service": "rfx-discuss-webhook"}


@Pipe
def configure_discuss_webhook(app):
    app.include_router(router)
    return app
