import asyncio
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .external_services.agent_client import create_agent_session, send_to_agent
from .external_services.whatsapp_client import (
    create_text_message,
    download_whatsapp_media,
    send_whatsapp_message,
)
from .models.messages import WhatsAppWebhookPayload
from .transcription import transcribe_audio_file
from .utils.app_config import AppType, config, AppSpecificConfig
from .utils.logging import get_logger
from .utils.model_utils import parse_webhook_payload

if TYPE_CHECKING:
    from .models.messages import WhatsAppMessage


async def send_message_to_agent(user: str, app_config: AppSpecificConfig, session_id: str, message: str) -> str:
    """Sends a message to the internal agent service and parses the response."""
    logger = get_logger(
        "agent_communication", {"app_name": app_config.app_name}
    )

    try:
        response_data = await send_to_agent(app_config, user, session_id, message)
        return response_data.get(
            "response", "Error: No se pudo extraer el texto de la respuesta."
        )
    except ValueError as e:
        logger.error(f"Configuration error: {e}", exc_info=True)
        return "Error: Servicio de agente no configurado."
    except Exception as e:
        logger.error(f"Error communicating with agent: {e}", exc_info=True)
        return "Error: Fallo la comunicación con el servicio del agente."


async def _send_whatsapp_acknowledgment(
    user_wa_id: str, message_text: str, app_config: AppSpecificConfig
) -> bool:
    """Send acknowledgment message to WhatsApp user."""
    logger = get_logger("whatsapp_ack", {"app_name": app_config.app_name})

    if not app_config.facebook_app_url or not app_config.wsp_token:
        logger.error("WhatsApp API URL or token is not configured.")
        return False

    try:
        message = create_text_message(message_text)
        await send_whatsapp_message(
            user_wa_id, message, f"{app_config.facebook_app_url}/messages", app_config.wsp_token
        )
        logger.info(f"Acknowledgment sent successfully to {user_wa_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send acknowledgment: {e}", exc_info=True)
        return False

async def _process_webhook_in_background(body: dict, app_type: AppType) -> None:
    """Process webhook in the background after sending an ACK."""
    app_config = config.aa if app_type == AppType.AA else config.pp

    webhook_payload = parse_webhook_payload(body)
    if not webhook_payload:
        logging.error("Failed to parse webhook payload.")
        return

    for sender_wa_id, message in webhook_payload.get_all_messages():
        try:
            await process_message(sender_wa_id, message, app_config)
        except Exception as e:
            logging.error(f"Error processing message {message.id}: {e}", exc_info=True)
            await _send_whatsapp_acknowledgment(
                sender_wa_id, "Error procesando mensaje.", app_config
            )

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

async def process_message(
    sender_wa_id: str, message: "WhatsAppMessage", app_config: AppSpecificConfig
) -> None:
    """Processes a single message from WhatsApp."""
    if message.type == "text":
        await _process_single_text_message(sender_wa_id, message, app_config)
    elif message.type == "audio" and message.audio:
        await handle_audio_message(sender_wa_id, message.audio.id, app_config)
    else:
        await _send_whatsapp_acknowledgment(
            sender_wa_id,
            "Solo puedo procesar mensajes de texto y audio. ¿En qué puedo ayudarte?",
            app_config,
        )

async def _process_single_text_message(
    sender_wa_id: str, message: "WhatsAppMessage", app_config: AppSpecificConfig
) -> None:
    """Process a single text message from WhatsApp."""
    app_name = app_config.app_name
    await create_agent_session(sender_wa_id, app_name, sender_wa_id)
    message_text = message.get_message_content() or ""
    agent_response = await send_message_to_agent(
        sender_wa_id, app_config, sender_wa_id, message_text
    )
    response_text = agent_response or "No pude procesar tu mensaje. Intenta de nuevo."
    await _send_whatsapp_acknowledgment(sender_wa_id, response_text, app_config)

async def handle_audio_message(
    phone: str, audio_id: str, app_config: AppSpecificConfig
) -> None:
    """Processes an audio message: downloads, transcribes, and responds."""
    api_url = app_config.facebook_app_url
    token = app_config.wsp_token

    if not api_url or not token:
        logging.error(
            f"Incomplete WhatsApp config for audio in {app_config.app_name}"
        )
        return

    try:
        audio_content = await download_whatsapp_media(audio_id, api_url, token)
        if not audio_content:
            await send_whatsapp_message(
                phone, create_text_message("No pude descargar tu audio."), f"{api_url}/messages", token
            )
            return

        transcript = await transcribe_audio_file(audio_content)
        if not transcript:
            await send_whatsapp_message(
                phone, create_text_message("No pude entender tu audio."), f"{api_url}/messages", token
            )
            return

        response = await send_message_to_agent(phone, app_config, phone, transcript)
        await send_whatsapp_message(
            phone, create_text_message(response), f"{api_url}/messages", token
        )
    except Exception as e:
        logging.error(f"Error processing audio: {e}", exc_info=True)
        await send_whatsapp_message(
            phone, create_text_message("Error procesando tu audio."), f"{api_url}/messages", token
        )