import hashlib
import hmac
import time

import httpx

from fluvius.data import serialize_mapping, serialize_json
from . import config, logger

TIMEOUT_SECONDS = 10


def _sign_payload(payload_bytes: bytes, timestamp: str, secret: str) -> str:
    """HMAC-SHA256 signature over ``timestamp.body``."""
    message = f"{timestamp}.".encode() + payload_bytes
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def _build_headers(payload_bytes: bytes, secret: str) -> dict:
    ts = str(int(time.time()))
    signature = _sign_payload(payload_bytes, ts, secret)
    return {
        "Content-Type": "application/json",
        "X-Webhook-Timestamp": ts,
        "X-Webhook-Signature": signature,
    }


async def deliver(callback_url: str, data: dict, secret: str | None = None):
    """POST *data* to *callback_url* with an HMAC-SHA256 signature.

    Headers sent:
        X-Webhook-Timestamp – unix epoch seconds when the request was built.
        X-Webhook-Signature – ``HMAC-SHA256(secret, "<timestamp>.<body>")``
    """
    secret = config.WEBHOOK_SECRET

    payload_bytes = serialize_json(data).encode()
    headers = _build_headers(payload_bytes, secret)

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(
                callback_url, content=payload_bytes, headers=headers
            )
    except httpx.HTTPError as exc:
        logger.error("Webhook delivery to %s failed: %s", callback_url, exc)
        return None

    if not response.is_success:
        logger.warning(
            "Webhook callback returned %s: %s",
            response.status_code,
            response.text[:500],
        )

    return response


async def dispatch_command(cmd, ctx_data, *, secret: str | None = None):
    """Deliver command data to the configured callback URL."""
    callback_url = config.CALLBACK_URL
    if not callback_url:
        return None

    data = {
        "event": cmd.command,
        "domain": cmd.domain,
        "resource": cmd.resource,
        "identifier": str(cmd.identifier),
        "payload": serialize_mapping(cmd.payload),
        "ctx_data": serialize_mapping(ctx_data),
    }

    return await deliver(callback_url, data, secret=secret)
