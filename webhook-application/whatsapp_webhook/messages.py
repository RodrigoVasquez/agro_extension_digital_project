import asyncio
import requests
import json
import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from .auth.google_auth import idtoken_from_metadata_server
from .sessions import create_session
from .utils.logging import get_logger
from .utils.app_config import config, AppType, WebhookConfig
from .utils.model_utils import (
    parse_webhook_payload,
    parse_agent_response,
    create_outgoing_text_message,
    create_agent_request
)
from .models.messages import WhatsAppWebhookPayload, AgentRequestPayload

if TYPE_CHECKING:
    from .models.messages import WhatsAppMessage


def send_message(user: str, app_name: str, session_id: str, message: str) -> str:
    """Sends a message to the internal agent service and parses the response."""
    logger = get_logger("agent_communication", {"app_name": app_name})
    webhook_config = config.get_webhook_config(AppType(app_name.lower()))
    
    if not config.agent_url:
        logger.error("APP_URL environment variable is not set")
        return "Error: Servicio de agente no configurado (URL)."

    try:
        id_token = idtoken_from_metadata_server(config.agent_url)
    except Exception as e:
        logger.error(f"Error generating ID token: {e}", exc_info=True)
        return "Error: No se pudo autenticar con el servicio del agente."

    agent_request = create_agent_request(
        app_name=webhook_config.agent_app_name,
        user_id=user,
        session_id=session_id,
        message_text=message
    )
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{config.agent_url}/run", headers=headers, json=agent_request.model_dump())
        response.raise_for_status()
        extracted_text = parse_agent_response(response.json())
        return extracted_text or "Error: No se pudo extraer el texto de la respuesta."
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to agent failed: {e}", exc_info=True)
        return "Error: Fallo la comunicación con el servicio del agente."
    except Exception as e:
        logger.error(f"Unexpected error parsing agent response: {e}", exc_info=True)
        return "Error: Error inesperado al procesar la respuesta del agente."

async def _send_whatsapp_acknowledgment(
    user_wa_id: str,
    message_text: str,
    webhook_config: WebhookConfig
) -> bool:
    """Send acknowledgment message to WhatsApp user."""
    logger = get_logger("whatsapp_ack", {"app_name": webhook_config.app_type.value})
    
    if not webhook_config.whatsapp_api_url or not webhook_config.whatsapp_token:
        logger.error("WhatsApp API URL or token is not configured.")
        return False

    outgoing_message = create_outgoing_text_message(user_wa_id, message_text)
    headers = {
        "Authorization": f"Bearer {webhook_config.whatsapp_token}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(f"{webhook_config.whatsapp_api_url}/messages", headers=headers, json=outgoing_message.model_dump())
        resp.raise_for_status()
        logger.info(f"Acknowledgment sent successfully to {user_wa_id}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send acknowledgment: {e}", exc_info=True)
        return False

async def _process_single_text_message(
    sender_wa_id: str,
    message: "WhatsAppMessage",
    webhook_config: WebhookConfig
) -> None:
    """Process a single text message from WhatsApp."""
    app_name = webhook_config.app_type.value
    create_session(sender_wa_id, app_name, sender_wa_id)
    message_text = message.get_message_content() or ""
    agent_response = send_message(sender_wa_id, app_name, sender_wa_id, message_text)
    response_text = agent_response or "No pude procesar tu mensaje. Intenta de nuevo."
    await _send_whatsapp_acknowledgment(sender_wa_id, response_text, webhook_config)

async def _process_non_text_message(
    sender_wa_id: str,
    message: "WhatsAppMessage",
    webhook_config: WebhookConfig
) -> None:
    """Process non-text messages from WhatsApp."""
    if message.type == "audio" and message.audio:
        await handle_audio_message(sender_wa_id, message.audio.id, webhook_config)
    else:
        await _send_whatsapp_acknowledgment(
            sender_wa_id,
            "Solo puedo procesar mensajes de texto y audio. ¿En qué puedo ayudarte?",
            webhook_config
        )

async def _process_webhook_in_background(body: dict, app_type: AppType) -> None:
    """Process webhook in the background after sending an ACK."""
    webhook_config = config.get_webhook_config(app_type)
    if validation_errors := webhook_config.validate():
        logging.error(f"Missing configuration for {app_type.value}: {validation_errors}")
        return

    webhook_payload = parse_webhook_payload(body)
    if not webhook_payload:
        logging.error("Failed to parse webhook payload.")
        return

    for sender_wa_id, message in webhook_payload.get_all_messages():
        try:
            if message.is_text_message():
                await _process_single_text_message(sender_wa_id, message, webhook_config)
            else:
                await _process_non_text_message(sender_wa_id, message, webhook_config)
        except Exception as e:
            logging.error(f"Error processing message {message.id}: {e}", exc_info=True)
            await _send_whatsapp_acknowledgment(sender_wa_id, "Error procesando mensaje.", webhook_config)

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

async def handle_audio_message(phone: str, audio_id: str, webhook_config: WebhookConfig) -> None:
    """Processes an audio message: downloads, transcribes, and responds."""
    from .external_services.whatsapp_client import download_whatsapp_media, send_whatsapp_message, create_text_message
    from .transcription import transcribe_audio_file

    api_url = webhook_config.whatsapp_api_url
    token = webhook_config.whatsapp_token
    app_name = webhook_config.app_type.value

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

        response = send_message(phone, app_name, phone, transcript)
        await send_whatsapp_message(phone, create_text_message(response), api_url, token)
    except Exception as e:
        logging.error(f"Error processing audio: {e}", exc_info=True)
        await send_whatsapp_message(phone, create_text_message("Error procesando tu audio."), api_url, token)