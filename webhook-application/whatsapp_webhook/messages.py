import asyncio
import requests
import json
import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from .auth.google_auth import idtoken_from_metadata_server
from .sessions import create_session
from .utils.logging import get_logger
from .utils.app_config import config, AppType, WhatsAppConfig
from .utils.model_utils import (
    parse_webhook_payload,
    parse_agent_response,
    create_outgoing_text_message,
    create_agent_request
)
from .models.messages import WhatsAppWebhookPayload, AgentRequestPayload

if TYPE_CHECKING:
    from .models.messages import WhatsAppMessage


def send_message(user: str, whatsapp_config: WhatsAppConfig, session_id: str, message: str) -> str:
    """Sends a message to the internal agent service and parses the response."""
    logger = get_logger("agent_communication", {"app_name": whatsapp_config.agent_app_name})
    
    logger.info("Starting agent communication", extra={
        "user_id": user,
        "session_id": session_id,
        "agent_app_name": whatsapp_config.agent_app_name,
        "message_length": len(message) if message else 0
    })
    
    # Get the complete agent run URL
    agent_run_url = whatsapp_config.get_agent_run_url()
    
    if not agent_run_url:
        logger.error("Agent URL is not configured", extra={
            "user_id": user,
            "session_id": session_id,
            "agent_app_name": whatsapp_config.agent_app_name,
            "base_url": config.agent.url
        })
        return "Error: Servicio de agente no configurado (URL)."

    logger.debug("Agent URL configured", extra={
        "user_id": user,
        "session_id": session_id,
        "agent_run_url": agent_run_url,
        "agent_app_name": whatsapp_config.agent_app_name
    })

    try:
        logger.debug("Generating ID token for agent authentication", extra={
            "user_id": user,
            "session_id": session_id,
            "target_url": config.agent.url
        })
        
        id_token = idtoken_from_metadata_server(config.agent.url)
        
        logger.debug("ID token generated successfully", extra={
            "user_id": user,
            "session_id": session_id,
            "token_length": len(id_token) if id_token else 0
        })
    except Exception as e:
        logger.error("Error generating ID token for agent authentication", extra={
            "user_id": user,
            "session_id": session_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "target_url": config.agent.url
        }, exc_info=True)
        return "Error: No se pudo autenticar con el servicio del agente."

    agent_request = create_agent_request(
        app_name=whatsapp_config.agent_app_name,
        user_id=user,
        session_id=session_id,
        message_text=message
    )
    
    logger.debug("Agent request created", extra={
        "user_id": user,
        "session_id": session_id,
        "agent_app_name": whatsapp_config.agent_app_name,
        "request_payload": agent_request.model_dump()
    })
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info("Sending request to agent", extra={
            "user_id": user,
            "session_id": session_id,
            "agent_run_url": agent_run_url,
            "agent_app_name": whatsapp_config.agent_app_name
        })
        
        response = requests.post(agent_run_url, headers=headers, json=agent_request.model_dump())
        
        logger.debug("Agent response received", extra={
            "user_id": user,
            "session_id": session_id,
            "status_code": response.status_code,
            "response_headers": dict(response.headers),
            "response_length": len(response.text) if response.text else 0,
            "agent_app_name": whatsapp_config.agent_app_name
        })
        
        response.raise_for_status()
        
        response_json = response.json()
        extracted_text = parse_agent_response(response_json)
        
        logger.info("Agent response processed successfully", extra={
            "user_id": user,
            "session_id": session_id,
            "agent_app_name": whatsapp_config.agent_app_name,
            "response_text_length": len(extracted_text) if extracted_text else 0,
            "extracted_successfully": bool(extracted_text)
        })
        
        return extracted_text or "Error: No se pudo extraer el texto de la respuesta."
        
    except requests.exceptions.RequestException as e:
        logger.error("HTTP request to agent failed", extra={
            "user_id": user,
            "session_id": session_id,
            "agent_run_url": agent_run_url,
            "agent_app_name": whatsapp_config.agent_app_name,
            "error": str(e),
            "error_type": type(e).__name__,
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            "response_text": getattr(e.response, 'text', None) if hasattr(e, 'response') else None
        }, exc_info=True)
        return "Error: Fallo la comunicación con el servicio del agente."
    except Exception as e:
        logger.error("Unexpected error during agent communication", extra={
            "user_id": user,
            "session_id": session_id,
            "agent_app_name": whatsapp_config.agent_app_name,
            "error": str(e),
            "error_type": type(e).__name__
        }, exc_info=True)
        return "Error: Error inesperado al procesar la respuesta del agente."

async def _send_whatsapp_acknowledgment(
    user_wa_id: str,
    message_text: str,
    whatsapp_config: WhatsAppConfig
) -> bool:
    """Send acknowledgment message to WhatsApp user."""
    logger = get_logger("whatsapp_ack", {"app_name": whatsapp_config.app_type.value})
    
    logger.info("Starting WhatsApp acknowledgment", extra={
        "user_wa_id": user_wa_id,
        "message_length": len(message_text) if message_text else 0,
        "app_type": whatsapp_config.app_type.value
    })
    
    # Debug logging para verificar la configuración
    logger.debug("WhatsApp configuration check", extra={
        "user_wa_id": user_wa_id,
        "api_url": whatsapp_config.api_url,
        "token_configured": bool(whatsapp_config.token),
        "token_length": len(whatsapp_config.token) if whatsapp_config.token else 0,
        "app_type": whatsapp_config.app_type.value
    })
    
    if not whatsapp_config.api_url or not whatsapp_config.token:
        logger.error("WhatsApp API URL or token is not configured", extra={
            "user_wa_id": user_wa_id,
            "api_url": whatsapp_config.api_url,
            "token_configured": bool(whatsapp_config.token),
            "app_type": whatsapp_config.app_type.value
        })
        return False

    outgoing_message = create_outgoing_text_message(user_wa_id, message_text)
    
    logger.debug("Outgoing message created", extra={
        "user_wa_id": user_wa_id,
        "message_payload": outgoing_message.model_dump(),
        "app_type": whatsapp_config.app_type.value
    })
    
    headers = {
        "Authorization": f"Bearer {whatsapp_config.token}",
        "Content-Type": "application/json"
    }
    
    try:
        whatsapp_url = f"{whatsapp_config.api_url}/messages"
        logger.info("Sending WhatsApp message", extra={
            "user_wa_id": user_wa_id,
            "whatsapp_url": whatsapp_url,
            "app_type": whatsapp_config.app_type.value
        })
        
        resp = requests.post(whatsapp_url, headers=headers, json=outgoing_message.model_dump())
        
        logger.debug("WhatsApp API response", extra={
            "user_wa_id": user_wa_id,
            "status_code": resp.status_code,
            "response_headers": dict(resp.headers),
            "response_text": resp.text[:500] if resp.text else None,
            "app_type": whatsapp_config.app_type.value
        })
        
        resp.raise_for_status()
        
        logger.info("WhatsApp acknowledgment sent successfully", extra={
            "user_wa_id": user_wa_id,
            "app_type": whatsapp_config.app_type.value,
            "status_code": resp.status_code
        })
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error("Failed to send WhatsApp acknowledgment", extra={
            "user_wa_id": user_wa_id,
            "app_type": whatsapp_config.app_type.value,
            "error": str(e),
            "error_type": type(e).__name__,
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            "response_text": getattr(e.response, 'text', None) if hasattr(e, 'response') else None,
            "whatsapp_url": f"{whatsapp_config.api_url}/messages"
        }, exc_info=True)
        return False

async def _process_single_text_message(
    sender_wa_id: str,
    message: "WhatsAppMessage",
    whatsapp_config: WhatsAppConfig
) -> None:
    """Process a single text message from WhatsApp."""
    logger = get_logger("message_processing", {"app_name": whatsapp_config.app_type.value})
    
    logger.info("Processing text message", extra={
        "sender_wa_id": sender_wa_id,
        "message_id": getattr(message, 'id', 'unknown'),
        "app_type": whatsapp_config.app_type.value,
        "agent_app_name": whatsapp_config.agent_app_name
    })
    
    app_name = whatsapp_config.app_type.value
    
    # Create session
    logger.debug("Creating session", extra={
        "sender_wa_id": sender_wa_id,
        "app_name": app_name,
        "session_id": sender_wa_id
    })
    
    create_session(sender_wa_id, app_name, sender_wa_id)
    
    message_text = message.get_message_content() or ""
    
    logger.debug("Sending message to agent", extra={
        "sender_wa_id": sender_wa_id,
        "message_length": len(message_text),
        "agent_app_name": whatsapp_config.agent_app_name
    })
    
    agent_response = send_message(sender_wa_id, whatsapp_config, sender_wa_id, message_text)
    response_text = agent_response or "No pude procesar tu mensaje. Intenta de nuevo."
    
    logger.debug("Sending WhatsApp acknowledgment", extra={
        "sender_wa_id": sender_wa_id,
        "response_length": len(response_text),
        "app_type": whatsapp_config.app_type.value
    })
    
    await _send_whatsapp_acknowledgment(sender_wa_id, response_text, whatsapp_config)
    
    logger.info("Text message processing completed", extra={
        "sender_wa_id": sender_wa_id,
        "app_type": whatsapp_config.app_type.value,
        "successful": True
    })

async def _process_non_text_message(
    sender_wa_id: str,
    message: "WhatsAppMessage",
    whatsapp_config: WhatsAppConfig
) -> None:
    """Process non-text messages from WhatsApp."""
    if message.type == "audio" and message.audio:
        await handle_audio_message(sender_wa_id, message.audio.id, whatsapp_config)
    else:
        await _send_whatsapp_acknowledgment(
            sender_wa_id,
            "Solo puedo procesar mensajes de texto y audio. ¿En qué puedo ayudarte?",
            whatsapp_config
        )

async def _process_webhook_in_background(body: dict, app_type: AppType) -> None:
    """Process webhook in the background after sending an ACK."""
    whatsapp_config = config.get_whatsapp_config(app_type)
    if validation_errors := whatsapp_config.validate():
        logging.error(f"Missing configuration for {app_type.value}: {validation_errors}")
        return

    webhook_payload = parse_webhook_payload(body)
    if not webhook_payload:
        logging.error("Failed to parse webhook payload.")
        return

    for sender_wa_id, message in webhook_payload.get_all_messages():
        try:
            if message.is_text_message():
                await _process_single_text_message(sender_wa_id, message, whatsapp_config)
            else:
                await _process_non_text_message(sender_wa_id, message, whatsapp_config)
        except Exception as e:
            logging.error(f"Error processing message {message.id}: {e}", exc_info=True)
            await _send_whatsapp_acknowledgment(sender_wa_id, "Error procesando mensaje.", whatsapp_config)

async def process_incoming_webhook_payload(body: dict, app_type: AppType) -> bool:
    """Core logic to process incoming webhook events from WhatsApp."""
    logging.info(f"Received webhook for {app_type.value} - sending immediate ACK.")
    asyncio.create_task(_process_webhook_in_background(body, app_type))
    return True

async def receive_message_aa(body: dict) -> bool:
    """Handles incoming messages for the AA application."""
    return await process_incoming_webhook_payload(body, AppType.AA)

async def receive_message_pp(body: dict) -> bool:
    """Handles incoming messages for the PP application."""
    return await process_incoming_webhook_payload(body, AppType.PP)

async def handle_audio_message(phone: str, audio_id: str, whatsapp_config: WhatsAppConfig) -> None:
    """Processes an audio message: downloads, transcribes, and responds."""
    from .external_services.whatsapp_client import download_whatsapp_media, send_whatsapp_message, create_text_message
    from .transcription import transcribe_audio_file

    api_url = whatsapp_config.api_url
    token = whatsapp_config.token
    app_name = whatsapp_config.app_type.value

    if not api_url or not token:
        logging.error(f"Incomplete WhatsApp config for audio in {app_name}")
        return

    try:
        audio_content = await download_whatsapp_media(audio_id, api_url, token)
        if not audio_content:
            await send_whatsapp_message(phone, create_text_message("No pude descargar tu audio."), api_url, token)
            return

        transcript = await transcribe_audio_file(audio_content)
        if not transcript:
            await send_whatsapp_message(phone, create_text_message("No pude entender tu audio."), api_url, token)
            return

        response = send_message(phone, whatsapp_config, phone, transcript)
        await send_whatsapp_message(phone, create_text_message(response), api_url, token)
    except Exception as e:
        logging.error(f"Error processing audio: {e}", exc_info=True)
        await send_whatsapp_message(phone, create_text_message("Error procesando tu audio."), api_url, token)