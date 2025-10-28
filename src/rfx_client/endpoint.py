from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header
from fluvius.data import logger
import hmac
import hashlib

from . import config


router = APIRouter(prefix="/webhook/<service_name>", tags=["webhooks"])


class WebhookHandler:
    """Handle incoming webhooks from PM services"""

    @staticmethod
    async def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
        if not secret:
            logger.warning("No webhook secret configured, skipping verification")
            return True
        expected_signature = hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)


# ========== FASTAPI ROUTES ==========


@router.post("/{service_name}")
async def linear_webhook(
    request: Request,
    x_linear_signature: Optional[str] = Header(None),
    x_linear_event: Optional[str] = Header(None),
):
    """
    Linear webhook endpoint

    Receives events from Linear via UAPI
    URL: POST /api/v1/webhook
    """
    try:
        # body = await request.body()

        # 1. Detect Linear Payload
        # 2. Init pm service Linear
        # 3. Process webhook payload

        # pmservice = PMService.init_client(provider=service_name)
        # payload = pmservice.verify_signature(request)
        # response = pmservice.handle_webhook(payload)

        # if response.external_type == "comment":
        #     response.external_id
        #     response.action
        #     response.external_data
        #     process_command()

        ...

        # Verify signature
        # webhook_secret = config.LINEAR_WEBHOOK_SECRET
        # if webhook_secret and x_linear_signature:
        #     is_valid = await WebhookHandler.verify_signature(
        #         body,
        #         x_linear_signature,
        #         webhook_secret
        #     )
        #     if not is_valid:
        #         logger.error("[Webhook] Invalid signature")
        #         raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse payload
        # payload = await request.json()
        #

        # command_payload = datadef.ProcessLinearWebhookPayload(
        #     event_type=x_linear_event
        #     or payload.get("event", {}).get("type", "Unknown"),
        #     data=payload,
        #     signature=x_linear_signature,
        # )

        # command_data = {
        #     "command": "process-linear-webhook",  # Tên command trong command.py
        #     "payload": command_payload.dict(),
        #     "context": {"realm": "system", "source": "webhook"},
        # }
        # domain = RFXClientDomain()
        # with domain.session(
        #     authorization=getattr(request.state, "auth_context", None),
        #     headers=dict(request.headers),
        #     transport=DomainTransport.FASTAPI,
        #     source=request.client.host,
        #     service_proxy=DomainServiceProxy(app.state),
        # ):
        #     command = domain.create_command(
        #         cmd_key,
        #         payload,
        #         aggroot=(
        #             resource,
        #             identifier,
        #             scope.get("domain_sid"),
        #             scope.get("domain_iid"),
        #         ),
        #     )

        #     responses = await domain.process_command(command)
        #     return {"data": responses, "status": "OK"}

        # # 5. GỌI COMMAND
        # responses = await domain.process_command(command_data)

        # 6. Trả về kết quả từ command
        # for resp in responses:
        #     if resp.get("_type") == "webhook-response":
        #         logger.info(f"[Webhook] Command processed: {resp.get('data')}")
        #         return resp.get("data")

        # return {"status": "ok_no_response"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Webhook] Error processing webhook: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())

        # Return 200 to avoid UAPI retries for application errors
        return {"status": "error", "error": str(e)}


@router.get("/health")
async def linear_webhook_health():
    """Health check endpoint for webhook"""
    return {
        "status": "ok",
        "service": "linear-webhook",
        "provider": config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
        "enabled": config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED,
    }
