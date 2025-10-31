from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header, Path
from fluvius.data import logger

from . import config, datadef
from rfx_integration.pm_service.base import PMService, WebhookEventType
from .domain import RFXClientDomain
from fluvius.domain.context import DomainTransport, DomainServiceProxy

router = APIRouter(prefix="/webhook", tags=["webhooks"])

WEBHOOK_COMMAND_MAP = {
    WebhookEventType.COMMENT_CREATED: "sync-comment-from-webhook",
    WebhookEventType.COMMENT_UPDATED: "sync-comment-from-webhook-change",
    WebhookEventType.COMMENT_DELETED: "sync-comment-from-webhook-change",
}


@router.post("/{service_name}")
async def linear_webhook(
    request: Request,
    x_linear_signature: Optional[str] = Header(None),
    x_linear_event: Optional[str] = Header(None),
    service_name: str = Path(...),
):
    """
    Linear webhook endpoint

    Receives events from Linear via UAPI
    URL: POST /api/v1/webhook
    """
    try:
        pmservice = PMService.init_client(provider=service_name)
        logger.info(f"[Webhook] Initialized {service_name} service")
        is_valid = await pmservice.verify_webhook_signature(request)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid signature")
        parsed_payload = await pmservice.parse_webhook_payload(request)
    except ValueError as e:
        logger.error(f"[Webhook] Invalid service: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Webhook] Payload parsing/verification error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payload or signature")

    try:
        webhook_response = await pmservice.handle_webhook(parsed_payload)
    except Exception as e:
        logger.error(f"[Webhook] Handler error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Handler failed: {str(e)}")

    try:
        await execute_webhook_command(
            request=request,
            webhook_response=webhook_response,
            service_name=service_name,
        )

        logger.info("[Webhook] ✓ Command executed successfully")

    except Exception as e:
        logger.error(f"[Webhook] Command execution error: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "event_type": webhook_response.event_type,
            "error": str(e),
        }


async def execute_webhook_command(
    request: Request, webhook_response, service_name: str
) -> Dict[str, Any]:
    """
    Execute appropriate command based on webhook event type

    Similar to FastAPIDomainManager command handling but for webhooks
    """
    event_type = webhook_response.event_type
    logger.info(f"[Webhook] Response: {webhook_response}")

    cmd_key = WEBHOOK_COMMAND_MAP.get(event_type)

    if not cmd_key:
        logger.warning(f"[Webhook] No command mapping for event: {event_type}")
        return {"status": "ignored", "reason": f"No command for {event_type}"}

    logger.info(f"[Webhook] Mapping {event_type} → command: {cmd_key}")
    external_data = webhook_response.external_data
    organization_id = None
    user_id = None
    realm = config.REALM_NAME

    if "comment" in event_type.lower():
        payload = datadef.SyncCommentFromWebhookPayload(
            action=webhook_response.action,
            provider=webhook_response.provider,
            external_id=webhook_response.external_id,
            external_data=webhook_response.external_data,
            target_id=webhook_response.target_id,
            target_type=webhook_response.target_type,
        )
        resource = "comment"
        identifier = webhook_response.external_id
        if "user" in external_data and isinstance(external_data["user"], dict):
            user_id = external_data["user"].get("id")
    else:
        return {"status": "error", "reason": f"Unknown resource type: {event_type}"}

    domain = RFXClientDomain()
    from types import SimpleNamespace

    authorization = SimpleNamespace(
        user=SimpleNamespace(
            _id=str(user_id) if user_id else None,
            id=str(user_id) if user_id else None,
        ),
        organization=SimpleNamespace(
            _id=str(organization_id) if organization_id else None,
            id=str(organization_id) if organization_id else None,
        ),
        realm=realm,
        profile=SimpleNamespace(
            _id=str(user_id) if user_id else None,
            id=str(user_id) if user_id else None,
        ),
        iamroles=[],
    )
    with domain.session(
        authorization=authorization,
        headers=dict(request.headers),
        transport=DomainTransport.FASTAPI,
        source=request.client.host,
        service_proxy=DomainServiceProxy(request.app.state),
    ):
        command = domain.create_command(
            cmd_key,
            payload,
            aggroot=(
                resource,
                identifier,
                None,
                None,
            ),
        )

        await domain.process_command(command)

        logger.info("[Webhook] Command processed successfully")


@router.get("/health")
async def linear_webhook_health():
    """Health check endpoint for webhook"""
    return {
        "status": "ok",
        "service": "linear-webhook",
        "provider": config.PROJECT_MANAGEMENT_INTEGRATION_PROVIDER,
        "enabled": config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED,
    }
