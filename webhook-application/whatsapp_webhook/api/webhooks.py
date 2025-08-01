"""
FastAPI router for WhatsApp webhook endpoints.
"""

from fastapi import APIRouter, Request, HTTPException, Query, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import json

from ..models.api_models import (
    WebhookVerificationResponse, 
    WebhookErrorResponse, 
    WebhookSuccessResponse
)
from ..utils.app_config import AppType, config
from ..utils.logging import get_logger
from ..messages import receive_message_aa, receive_message_pp

# Create router
router = APIRouter(prefix="", tags=["webhooks"])

# Get logger for this module
logger = get_logger("webhook_router")


async def verify_webhook(
    app_type: AppType,
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"), 
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
) -> JSONResponse:
    """
    Generic webhook verification handler.
    
    Args:
        app_type: Type of application (AA or PP)
        hub_mode: Verification mode from WhatsApp
        hub_verify_token: Token to verify
        hub_challenge: Challenge string to return
        
    Returns:
        JSONResponse with challenge or error
    """
    webhook_config = config.get_webhook_config(app_type)
    app_name = app_type.value.upper()
    
    logger.log_webhook_verification(
        app_name, 
        hub_mode or "None", 
        False,  # Will update based on result
        {
            "token_provided": hub_verify_token is not None,
            "challenge_provided": hub_challenge is not None
        }
    )
    
    if hub_mode == "subscribe" and hub_verify_token == webhook_config.verify_token:
        if not hub_challenge:
            logger.warning(f"{app_name} Webhook verification failed: No challenge provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge parameter required"
            )
        
        try:
            challenge_int = int(hub_challenge)
            logger.log_webhook_verification(app_name, hub_mode, True, {"challenge": challenge_int})
            return JSONResponse(content=challenge_int)
        except ValueError:
            logger.warning(f"{app_name} Webhook verification failed: Invalid challenge format")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge must be a valid integer"
            )
    else:
        logger.log_webhook_verification(
            app_name, 
            hub_mode or "None", 
            False,
            {
                "expected_mode": "subscribe",
                "token_match": hub_verify_token == webhook_config.verify_token
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook verification failed"
        )


async def handle_webhook_post(
    app_type: AppType,
    request: Request
) -> JSONResponse:
    """
    Generic webhook POST handler.
    
    Args:
        app_type: Type of application (AA or PP)
        request: FastAPI request object
        
    Returns:
        JSONResponse with success status
    """
    app_name = app_type.value.upper()
    
    logger.log_webhook_processing(app_name, "received", {"endpoint": str(request.url)})
    
    try:
        body = await request.json()
        logger.log_webhook_processing(app_name, "json_parsed", {"body_size": len(str(body))})
        
        # Route to appropriate message handler
        if app_type == AppType.AA:
            await receive_message_aa(body)
        elif app_type == AppType.PP:
            await receive_message_pp(body)
        else:
            raise ValueError(f"Unknown app type: {app_type}")
        
        logger.log_webhook_processing(app_name, "completed")
        
        # WhatsApp expects a 200 OK quickly
        return JSONResponse(
            content={"status": "ok"}, 
            status_code=status.HTTP_200_OK
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"{app_name} Failed to decode JSON from webhook request", {"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format"
        )
    except Exception as e:
        logger.error(
            f"{app_name} Unexpected error occurred in webhook handler", 
            {"error": str(e)},
            exc_info=True
        )
        # Still return 200 OK to WhatsApp to prevent retries for errors during our processing
        return JSONResponse(
            content={"status": "ok"}, 
            status_code=status.HTTP_200_OK
        )


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
    return await handle_webhook_post(AppType.AA, request)


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
    return await handle_webhook_post(AppType.PP, request)
