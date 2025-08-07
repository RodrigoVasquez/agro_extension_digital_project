"""
FastAPI router for WhatsApp webhook endpoints.
"""

from fastapi import APIRouter, Request, HTTPException, Query, status
from fastapi.responses import JSONResponse
from typing import Optional
import json

from ..models.api_models import WebhookSuccessResponse, WebhookVerificationResponse
from ..utils.app_config import AppType, config, WhatsAppConfig
from ..utils.logging import get_logger
from ..messages import receive_message_aa, receive_message_pp

router = APIRouter(prefix="", tags=["webhooks"])
logger = get_logger("webhook_router")

async def _verify_webhook(app_type: AppType, params: Request.query_params) -> JSONResponse:
    """Generic webhook verification handler."""
    webhook_config = config.get_webhook_config(app_type)
    app_name = webhook_config.app_name or app_type.value.upper()
    
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    log_extra = {"token_provided": bool(token), "challenge_provided": bool(challenge)}
    logger.log_webhook_verification(app_name, mode or "None", False, log_extra)

    if mode == "subscribe" and token == webhook_config.verify_token:
        if not challenge or not challenge.isdigit():
            logger.warning(f"{app_name} Webhook verification failed: Invalid challenge")
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid challenge")
        
        logger.log_webhook_verification(app_name, mode, True, {"challenge": challenge})
        return JSONResponse(content=int(challenge))
    
    logger.warning(f"{app_name} Webhook verification failed: Token or mode mismatch")
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Webhook verification failed")

async def _handle_webhook_post(app_type: AppType, request: Request) -> JSONResponse:
    """Generic webhook POST handler."""
    app_name = config.get_webhook_config(app_type).app_name or app_type.value.upper()
    logger.info(f"Processing webhook for {app_name}", extra={"endpoint": str(request.url)})

    try:
        body = await request.json()
        handler = receive_message_aa if app_type == AppType.AA else receive_message_pp
        await handler(body)
        logger.info(f"Webhook for {app_name} processed successfully")
        return JSONResponse({"status": "ok"})
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON received for {app_name}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid JSON format")
    except Exception as e:
        logger.error(f"Error processing webhook for {app_name}: {e}", exc_info=True)
        # Always return 200 OK to WhatsApp to prevent retries
        return JSONResponse({"status": "ok"})


# AA Webhook endpoints
@router.get("/estandar_aa_webhook", response_model=WebhookVerificationResponse)
async def verify_aa_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """Verify AA webhook subscription."""
    return await verify_webhook(AppType.AA, hub_mode, hub_verify_token, hub_challenge)


@router.post("/estandar_aa_webhook", response_model=WebhookSuccessResponse)
async def handle_estandar_aa_webhook(request: Request):
    """Handle incoming AA webhook messages."""
    return await _handle_webhook_post(AppType.AA, request)


# PP Webhook endpoints  
@router.get("/estandar_pp_webhook", response_model=WebhookVerificationResponse)
async def verify_pp_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """Verify PP webhook subscription."""
    return await verify_webhook(AppType.PP, hub_mode, hub_verify_token, hub_challenge)


@router.post("/estandar_pp_webhook", response_model=WebhookSuccessResponse)
async def handle_estandar_pp_webhook(request: Request):
    """Handle incoming PP webhook messages."""
    return await _handle_webhook_post(AppType.PP, request)
