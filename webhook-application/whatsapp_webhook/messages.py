import asyncio
import requests
import os
import json
import re # Not strictly needed for the new send_message but kept for now
import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from .auth.google_auth import idtoken_from_metadata_server # Updated import
from .sessions import create_session # Relative import
from .utils.logging import get_logger # New import
from .utils.helpers import sanitize_user_id # New import
from .utils.config import get_agent_app_name # Import for app name mapping
from .utils.model_utils import (  # New import for domain models
    parse_webhook_payload,
    parse_agent_response,
    create_outgoing_text_message,
    create_processing_context,
    create_agent_request
)
from .models.messages import WhatsAppWebhookPayload, AgentRequestPayload  # Domain models

if TYPE_CHECKING:
    from .models.messages import WhatsAppMessage

APP_URL = os.getenv("APP_URL")

def send_message(user: str, app_name: str, session_id: str, message: str) -> str:
    """
    Sends a message to the internal agent service and parses the response.
    
    Args:
        user: User identifier
        app_name: Application name 
        session_id: Session identifier
        message: Message text to send
        
    Returns:
        Agent response text or error message
    """
    logger = get_logger("agent_communication", {"app_name": app_name})
    
    # Mapear nombre de app a nombre esperado por el agente
    agent_app_name = get_agent_app_name(app_name)
    
    if not APP_URL:
        logger.error("APP_URL environment variable is not set")
        return "Error: Servicio de agente no configurado (URL)."

    # Get authentication token
    try:
        logger.info("Fetching ID token for agent service", extra={"user_id": user})
        id_token = idtoken_from_metadata_server(APP_URL)
        logger.info("ID token fetched successfully", extra={"user_id": user})
    except Exception as e:
        logger.error(f"Error generating ID token: {e}", extra={"user_id": user}, exc_info=True)
        return "Error: No se pudo autenticar con el servicio del agente. Por favor contacte al administrador."

    # Create agent request using Pydantic model
    try:
        agent_request = create_agent_request(
            app_name=agent_app_name,  # Usar el nombre mapeado
            user_id=user,
            session_id=session_id,
            message_text=message,
            streaming=False
        )
        payload_dict = agent_request.model_dump()
    except Exception as e:
        logger.error(f"Error creating agent request payload: {e}", extra={"user_id": user}, exc_info=True)
        return "Error: No se pudo crear la solicitud para el agente."

    # Send request to agent service
    session_url = f"{APP_URL}/run"
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }

    logger.log_agent_message_request(user, app_name, agent_app_name, session_url)
    logger.log_agent_request(user, app_name, payload_dict)
    
    try:
        response = requests.post(session_url, headers=headers, json=payload_dict)
        response.raise_for_status()
        
        logger.debug("Raw response from agent", extra={"user_id": user, "response_size": len(response.text)})
        response_data = response.json()

        # Parse agent response using utility function
        extracted_text = parse_agent_response(response_data)
        if extracted_text:
            logger.info("Successfully extracted text from agent response", extra={"user_id": user})
            return extracted_text
        else:
            logger.warning("Could not extract text from agent response", extra={"user_id": user})
            return "Error: No se pudo extraer el texto de la respuesta del agente."
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from agent: {e}", extra={"user_id": user}, exc_info=True)
        return "Error: La respuesta del agente no es un JSON válido."
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to agent failed: {e}", extra={"user_id": user}, exc_info=True)
        return "Error: Fallo la comunicación con el servicio del agente."
    except Exception as e:
        logger.error(f"Unexpected error while parsing agent response: {e}", extra={"user_id": user}, exc_info=True)
        return "Error: Error inesperado al procesar la respuesta del agente."

async def _send_whatsapp_acknowledgment(
    user_wa_id: str,
    message_text: str,
    app_name: str,
    whatsapp_api_url: str,
    wsp_token: str,
    message_context: str = "message"
) -> bool:
    """
    Send acknowledgment message to WhatsApp user.
    
    Args:
        user_wa_id: WhatsApp user ID
        message_text: Text to send
        app_name: Application name
        whatsapp_api_url: WhatsApp API endpoint URL
        wsp_token: WhatsApp API token
        message_context: Context for logging (e.g., "text message", "error")
        
    Returns:
        True if sent successfully, False otherwise
    """
    logger = get_logger("whatsapp_ack", {"app_name": app_name})
    
    try:
        # Create outgoing message
        outgoing_message = create_outgoing_text_message(user_wa_id, message_text)
        whatsapp_payload = outgoing_message.model_dump()
        
        headers = {
            "Authorization": f"Bearer {wsp_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Sending acknowledgment for {message_context}", extra={"user_id": user_wa_id})
        
        # Send to WhatsApp API - construct correct URL for messages
        whatsapp_url = f"{whatsapp_api_url}/messages"
        resp = requests.post(whatsapp_url, headers=headers, json=whatsapp_payload)
        
        # Log response
        response_json = None
        if resp.headers.get('content-type', '').startswith('application/json'):
            try:
                response_json = resp.json()
            except json.JSONDecodeError:
                pass
                
        logger.log_whatsapp_response(user_wa_id, app_name, resp.status_code, response_json)
        resp.raise_for_status()
        
        logger.info(f"Acknowledgment sent successfully for {message_context}", extra={"user_id": user_wa_id})
        return True
        
    except Exception as e:
        logger.error(f"Failed to send acknowledgment for {message_context}: {e}", 
                    extra={"user_id": user_wa_id}, exc_info=True)
        return False

async def _process_single_text_message(
    sender_wa_id: str,
    message: "WhatsAppMessage",
    app_name: str,
    whatsapp_api_url: str,
    wsp_token: str
) -> None:
    """
    Process a single text message from WhatsApp.
    Processes with agent and responds (no visible ACK to user).
    """
    logger = get_logger("message_processing", {"app_name": app_name})
    
    # Process and respond directly (no visible ACK to user)
    try:
        create_session(sender_wa_id, app_name, sender_wa_id)
        
        # Get message text from the message object
        message_text = message.get_message_content()
        if not message_text:
            raise ValueError("No message content found")
        
        # Process with agent using send_message function
        agent_response = send_message(
            user=sender_wa_id,
            app_name=app_name,
            session_id=sender_wa_id,
            message=message_text
        )
        
        # Send agent response or fallback (this is the only visible message)
        response_text = agent_response or "No pude procesar tu mensaje. Intenta de nuevo."
        
        await _send_whatsapp_acknowledgment(
            user_wa_id=sender_wa_id,
            message_text=response_text,
            app_name=app_name,
            whatsapp_api_url=whatsapp_api_url,
            wsp_token=wsp_token,
            message_context="response"
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", extra={"user_id": sender_wa_id})
        
        await _send_whatsapp_acknowledgment(
            user_wa_id=sender_wa_id,
            message_text="Error procesando mensaje. Intenta más tarde.",
            app_name=app_name,
            whatsapp_api_url=whatsapp_api_url,
            wsp_token=wsp_token,
            message_context="error"
        )
def _validate_webhook_config(app_name_env_var: str, facebook_app_env_var: str) -> Optional[Dict[str, str]]:
    """
    Validate required environment variables for webhook processing.
    
    Args:
        app_name_env_var: Environment variable name for app name
        facebook_app_env_var: Environment variable name for Facebook app URL
        
    Returns:
        Dictionary with configuration values or None if validation fails
    """
    app_name = os.getenv(app_name_env_var)
    whatsapp_api_url = os.getenv(facebook_app_env_var)
    wsp_token = os.getenv("WSP_TOKEN")

    if not app_name:
        logging.error(f"Environment variable {app_name_env_var} not set. Cannot process webhook.")
        return None
    if not whatsapp_api_url:
        logging.error(f"Environment variable {facebook_app_env_var} not set. Cannot process webhook.")
        return None
    if not wsp_token:
        logging.error("Environment variable WSP_TOKEN not set. Cannot process webhook.")
        return None

    return {
        "app_name": app_name,
        "whatsapp_api_url": whatsapp_api_url,
        "wsp_token": wsp_token
    }


async def _process_webhook_in_background(
    body: dict, 
    app_name_env_var: str, 
    facebook_app_env_var: str
) -> None:
    """
    Process webhook in background after ACK to Facebook.
    Handles validation, parsing, and message processing.
    
    Args:
        body: WhatsApp webhook payload
        app_name_env_var: Environment variable name for app name
        facebook_app_env_var: Environment variable name for Facebook app URL
    """
    logger = get_logger("background_webhook_processing")
    logger.info("Starting background webhook processing")
    
    try:
        # STEP 1: Validate configuration
        config = _validate_webhook_config(app_name_env_var, facebook_app_env_var)
        if not config:
            logger.error("Failed to validate webhook configuration in background")
            return

        app_name = config["app_name"]
        logger.info(f"Background processing webhook for app: {app_name}")

        # STEP 2: Parse webhook payload using Pydantic model
        webhook_payload = parse_webhook_payload(body)
        if not webhook_payload:
            logger.error(f"Failed to parse webhook payload for app {app_name} in background")
            return

        # STEP 3: Extract all messages using the domain model
        all_messages = webhook_payload.get_all_messages()
        
        if not all_messages:
            logger.info(f"No messages found in webhook payload for app {app_name}")
            return

        # STEP 4: Process messages
        logger.info(f"Background processing {len(all_messages)} messages for app {app_name}")
        await _process_messages_in_background(all_messages, config)
        
    except Exception as e:
        logger.error(f"Unexpected error in background webhook processing: {e}", exc_info=True)


async def _process_messages_in_background(
    all_messages: List[tuple],
    config: Dict[str, str]
) -> None:
    """
    Process messages in background after ACK to Facebook.
    
    Args:
        all_messages: List of (sender_wa_id, message) tuples
        config: Validated configuration dictionary
    """
    app_name = config["app_name"]
    logger = get_logger("background_processing", {"app_name": app_name})
    
    logger.info(f"Starting background processing of {len(all_messages)} messages for app {app_name}")
    
    # Process each message based on its type
    for sender_wa_id, message in all_messages:
        message_id = message.id
        message_type = message.type
        
        logger.info(f"Background processing {message_type} message (ID: {message_id}) from user {sender_wa_id}")
        
        try:
            if message.is_text_message():
                # Process text messages with the agent
                await _process_single_text_message(
                    sender_wa_id=sender_wa_id,
                    message=message,
                    app_name=app_name,
                    whatsapp_api_url=config["whatsapp_api_url"],
                    wsp_token=config["wsp_token"]
                )
            else:
                # Handle non-text messages
                await _process_non_text_message(
                    sender_wa_id=sender_wa_id,
                    message=message,
                    app_name=app_name,
                    whatsapp_api_url=config["whatsapp_api_url"],
                    wsp_token=config["wsp_token"]
                )
        except Exception as e:
            logger.error(f"Error in background processing message {message_id} from {sender_wa_id}: {e}", exc_info=True)
            # Send acknowledgment even if processing fails
            try:
                await _send_whatsapp_acknowledgment(
                    user_wa_id=sender_wa_id,
                    message_text="Disculpa, hubo un error procesando tu mensaje. Por favor intenta de nuevo.",
                    app_name=app_name,
                    whatsapp_api_url=config["whatsapp_api_url"],
                    wsp_token=config["wsp_token"],
                    message_context="error recovery"
                )
            except Exception as ack_error:
                logger.error(f"Failed to send error acknowledgment to {sender_wa_id}: {ack_error}", exc_info=True)
    
    logger.info(f"Background processing completed for app {app_name}")


async def process_incoming_webhook_payload(body: dict, app_name_env_var: str, facebook_app_env_var: str) -> bool:
    """
    Core logic to process incoming webhook events from WhatsApp.
    ACKs immediately to Facebook first, then validates and processes messages in background.
    
    Args:
        body: WhatsApp webhook payload
        app_name_env_var: Environment variable name for app name
        facebook_app_env_var: Environment variable name for Facebook app URL
        
    Returns:
        bool: Always True for immediate ACK to Facebook (HTTP 200)
    """
    # STEP 1: ALWAYS ACK TO FACEBOOK FIRST - No matter what happens
    logging.info("Received webhook - sending immediate ACK to Facebook")
    
    # Start background processing without waiting for completion
    asyncio.create_task(_process_webhook_in_background(body, app_name_env_var, facebook_app_env_var))
    
    # Return True immediately for Facebook ACK - CRITICAL for preventing retries
    logging.info("Webhook ACK sent immediately to Facebook")
    return True


async def _process_non_text_message(
    sender_wa_id: str,
    message: "WhatsAppMessage",
    app_name: str,
    whatsapp_api_url: str,
    wsp_token: str
) -> None:
    """
    Process non-text messages from WhatsApp.
    Handles audio messages or sends info about text-only support.
    """
    logger = get_logger("message_processing", {"app_name": app_name})
    
    if message.type == "audio" and hasattr(message, 'audio') and message.audio:
        # Procesar mensaje de audio
        session_id = sender_wa_id  # Usar sender_wa_id como session_id
        create_session(sender_wa_id, app_name, session_id)
        await handle_audio_message(sender_wa_id, message.audio.id, app_name, session_id)
    else:
        # Send info message for other non-text types
        await _send_whatsapp_acknowledgment(
            user_wa_id=sender_wa_id,
            message_text="Solo puedo procesar mensajes de texto y audio. ¿En qué puedo ayudarte?",
            app_name=app_name,
            whatsapp_api_url=whatsapp_api_url,
            wsp_token=wsp_token,
            message_context="info"
        )


async def receive_message_aa(body: dict) -> bool:
    """
    Handles incoming messages for Estandar AA application.
    
    Args:
        body: WhatsApp webhook payload dictionary
        
    Returns:
        bool: True for HTTP 200 ACK to Facebook, False for HTTP 500
    """
    logger = get_logger("webhook_aa")
    logger.info("Processing AA webhook request")
    
    try:
        result = await process_incoming_webhook_payload(
            body=body,
            app_name_env_var="ESTANDAR_AA_APP_NAME",
            facebook_app_env_var="ESTANDAR_AA_FACEBOOK_APP"
        )
        logger.info(f"AA webhook processing result: {result}")
        return result
    except Exception as e:
        logger.error(f"Unexpected error in AA webhook processing: {e}", exc_info=True)
        # Return True to ACK to Facebook even on unexpected errors to prevent retries
        return True


async def receive_message_pp(body: dict) -> bool:
    """
    Handles incoming messages for Estandar PP application.
    
    Args:
        body: WhatsApp webhook payload dictionary
        
    Returns:
        bool: True for HTTP 200 ACK to Facebook, False for HTTP 500
    """
    logger = get_logger("webhook_pp")
    logger.info("Processing PP webhook request")
    
    try:
        result = await process_incoming_webhook_payload(
            body=body,
            app_name_env_var="ESTANDAR_PP_APP_NAME",
            facebook_app_env_var="ESTANDAR_PP_FACEBOOK_APP"
        )
        logger.info(f"PP webhook processing result: {result}")
        return result
    except Exception as e:
        logger.error(f"Unexpected error in PP webhook processing: {e}", exc_info=True)
        # Return True to ACK to Facebook even on unexpected errors to prevent retries
        return True


async def handle_audio_message(phone: str, audio_id: str, app_name: str, session_id: str) -> None:
    """Procesa mensaje de audio: descarga, transcribe y responde."""
    from .external_services.whatsapp_client import download_media, send_whatsapp_message, create_text_message
    from .transcription import transcribe_audio_file
    from .utils.config import get_whatsapp_config
    
    config = get_whatsapp_config(app_name)
    
    try:
        # Descargar audio usando la URL base - download_media construirá /{audio_id}
        audio_content = await download_media(audio_id, config["api_url"], config["token"])
        if not audio_content:
            await send_whatsapp_message(phone, create_text_message("No pude descargar tu audio."), config["api_url"], config["token"])
            return
        
        # Transcribir
        transcript = await transcribe_audio_file(audio_content)
        if not transcript:
            await send_whatsapp_message(phone, create_text_message("No pude entender tu audio."), config["api_url"], config["token"])
            return
        
        # Procesar con agente
        response = send_message(phone, app_name, session_id, transcript)
        await send_whatsapp_message(phone, create_text_message(response), config["api_url"], config["token"])
        
    except Exception as e:
        logging.error(f"Error procesando audio: {e}")
        await send_whatsapp_message(phone, create_text_message("Error procesando tu audio."), config["api_url"], config["token"])