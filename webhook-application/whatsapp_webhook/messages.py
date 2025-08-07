import asyncio
import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from .external_services.agent_client import send_to_agent, create_agent_session
from .external_services.whatsapp_client import send_whatsapp_message, create_text_message, download_whatsapp_media
from .transcription import transcribe_audio_file
from .utils.logging import get_logger
from .utils.app_config import config, AppType, WhatsAppConfig
from .utils.model_utils import parse_webhook_payload
from .models.messages import WhatsAppWebhookPayload

if TYPE_CHECKING:
    from .models.messages import WhatsAppMessage


async def send_message_to_agent(user: str, whatsapp_config: WhatsAppConfig, session_id: str, message: str) -> str:
    """Sends a message to the internal agent service and parses the response."""
    logger = get_logger("agent_communication", {"app_name": whatsapp_config.agent_app_name})
    
    try:
        response_data = await send_to_agent(whatsapp_config, user, session_id, message)
        return response_data.get("response", "Error: No se pudo extraer el texto de la respuesta.")
    except ValueError as e:
        logger.error(f"Configuration error: {e}", exc_info=True)
        return "Error: Servicio de agente no configurado."
    except Exception as e:
        logger.error(f"Error communicating with agent: {e}", exc_info=True)
        return "Error: Fallo la comunicación con el servicio del agente."

async def _send_whatsapp_acknowledgment(
    user_wa_id: str,
    message_text: str,
    whatsapp_config: WhatsAppConfig
) -> bool:
    """Send acknowledgment message to WhatsApp user."""
    logger = get_logger("whatsapp_ack", {"app_name": whatsapp_config.app_type.value})
    
    if not whatsapp_config.api_url or not whatsapp_config.token:
        logger.error("WhatsApp API URL or token is not configured.")
        return False

    try:
        message = create_text_message(message_text)
        await send_whatsapp_message(user_wa_id, message, f"{whatsapp_config.api_url}/messages", whatsapp_config.token)
        logger.info(f"Acknowledgment sent successfully to {user_wa_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send acknowledgment: {e}", exc_info=True)
        return False

async def _process_single_text_message(
    sender_wa_id: str,
    message: "WhatsAppMessage",
    whatsapp_config: WhatsAppConfig
) -> None:
    """Process a single text message from WhatsApp."""
    app_name = whatsapp_config.app_type.value
    await create_agent_session(sender_wa_id, app_name, sender_wa_id)
    message_text = message.get_message_content() or ""
    agent_response = await send_message_to_agent(sender_wa_id, whatsapp_config, sender_wa_id, message_text)
    response_text = agent_response or "No pude procesar tu mensaje. Intenta de nuevo."
    await _send_whatsapp_acknowledgment(sender_wa_id, response_text, whatsapp_config)

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
    api_url = whatsapp_config.api_url
    token = whatsapp_config.token
    app_name = whatsapp_config.app_type.value

    if not api_url or not token:
        logging.error(f"Incomplete WhatsApp config for audio in {app_name}")
        return

    try:
        audio_content = await download_whatsapp_media(audio_id, api_url, token)
        if not audio_content:
            await send_whatsapp_message(phone, create_text_message("No pude descargar tu audio."), f"{api_url}/messages", token)
            return

        transcript = await transcribe_audio_file(audio_content)
        if not transcript:
            await send_whatsapp_message(phone, create_text_message("No pude entender tu audio."), f"{api_url}/messages", token)
            return

        response = await send_message_to_agent(phone, whatsapp_config, phone, transcript)
        await send_whatsapp_message(phone, create_text_message(response), f"{api_url}/messages", token)
    except Exception as e:
        logging.error(f"Error processing audio: {e}", exc_info=True)
        await send_whatsapp_message(phone, create_text_message("Error procesando tu audio."), f"{api_url}/messages", token)