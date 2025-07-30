import requests
import os
import json
import re # Not strictly needed for the new send_message but kept for now
import logging
from typing import Optional, Dict, Any, List

from .auth.google_auth import idtoken_from_metadata_server # Updated import
from .sessions import create_session # Relative import
from .utils.logging import get_logger # New import
from .utils.helpers import sanitize_user_id # New import
from .utils.model_utils import (  # New import for domain models
    parse_webhook_payload,
    parse_agent_response,
    create_outgoing_text_message,
    create_processing_context,
    create_agent_request
)
from .models.messages import WhatsAppWebhookPayload, AgentRequestPayload  # Domain models

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
            app_name=app_name,
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

async def _process_single_text_message(
    user_wa_id: str, 
    message_text: str, 
    app_name: str, 
    whatsapp_api_url: str, 
    wsp_token: str
) -> None:
    """
    Processes a single text message from WhatsApp.
    
    Args:
        user_wa_id: WhatsApp user ID
        message_text: Text content of the message
        app_name: Application name
        whatsapp_api_url: WhatsApp API endpoint URL
        wsp_token: WhatsApp API token
    """
    logger = get_logger("message_processing", {"app_name": app_name})
    
    logger.log_message_received("text", user_wa_id, app_name, {"message_length": len(message_text)})
    
    # Create user session
    try:
        create_session(user_wa_id, app_name, user_wa_id)  # session_id = user_wa_id
        logger.info("Session created successfully", extra={"user_id": user_wa_id})
    except Exception as e:
        logger.error(f"Failed to create session: {e}", extra={"user_id": user_wa_id}, exc_info=True)
        return

    # Get response from agent service
    response_from_service = send_message(user_wa_id, app_name, user_wa_id, message_text)
    
    # Create and send WhatsApp response using Pydantic model
    try:
        outgoing_message = create_outgoing_text_message(user_wa_id, response_from_service)
        whatsapp_payload = outgoing_message.model_dump()
        
        headers = {
            "Authorization": f"Bearer {wsp_token}",
            "Content-Type": "application/json"
        }
        
        logger.info("Sending response to WhatsApp", extra={"user_id": user_wa_id})
        logger.debug("WhatsApp payload prepared", extra={
            "user_id": user_wa_id, 
            "payload_size": len(str(whatsapp_payload))
        })
        
        # Send to WhatsApp API
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
        
        logger.info("WhatsApp message sent successfully", extra={"user_id": user_wa_id})
        
    except Exception as e:
        if isinstance(e, requests.exceptions.RequestException):
            logger.error(f"Error posting to WhatsApp API: {e}", extra={"user_id": user_wa_id}, exc_info=True)
        else:
            logger.error(f"Unexpected error in message processing: {e}", extra={"user_id": user_wa_id}, exc_info=True)


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


def _extract_text_messages_from_change(change: Dict[str, Any], app_name: str) -> List[Dict[str, str]]:
    """
    Extract text messages from a webhook change object.
    
    Args:
        change: WhatsApp webhook change object
        app_name: Application name for logging
        
    Returns:
        List of dictionaries with user_wa_id and message_text
    """
    messages = []
    
    if change.get('field') != 'messages':
        return messages
        
    value = change.get('value', {})
    
    # Extract sender WhatsApp ID
    user_wa_id = None
    if 'contacts' in value and isinstance(value['contacts'], list) and value['contacts']:
        user_wa_id = value['contacts'][0].get('wa_id')

    if not user_wa_id:
        logging.warning(f"No wa_id found in contacts for app {app_name}. Value: {value}")
        return messages

    # Extract messages
    if 'messages' in value and isinstance(value['messages'], list):
        for message_obj in value['messages']:
            message_id = message_obj.get('id', 'N/A')
            
            if message_obj.get('type') == 'text':
                message_text_data = message_obj.get('text', {})
                message_text = message_text_data.get('body')

                if message_text:
                    messages.append({
                        "user_wa_id": user_wa_id,
                        "message_text": message_text,
                        "message_id": message_id
                    })
                else:
                    logging.warning(f"No text body in message (ID: {message_id}) for user {user_wa_id}, app {app_name}")
            else:
                logging.info(f"Skipping non-text message (ID: {message_id}, Type: {message_obj.get('type')}) for user {user_wa_id}, app {app_name}")
    else:
        logging.warning(f"No 'messages' array in 'value' for user {user_wa_id}, app {app_name}")

    return messages


async def _process_webhook_entry(entry: Dict[str, Any], config: Dict[str, str]) -> None:
    """
    Process a single webhook entry.
    
    Args:
        entry: WhatsApp webhook entry object
        config: Validated configuration dictionary
    """
    entry_id = entry.get('id', 'N/A')
    app_name = config["app_name"]
    
    logging.debug(f"Processing entry ID: {entry_id} for app {app_name}")
    
    if 'changes' not in entry or not entry['changes']:
        logging.debug(f"No 'changes' in entry {entry_id} for app {app_name}")
        return

    for change in entry['changes']:
        field = change.get('field', 'N/A')
        logging.debug(f"Processing change field: {field} in entry {entry_id} for app {app_name}")
        
        # Extract text messages from this change
        text_messages = _extract_text_messages_from_change(change, app_name)
        
        # Process each text message
        for msg_data in text_messages:
            try:
                await _process_single_text_message(
                    user_wa_id=msg_data["user_wa_id"],
                    message_text=msg_data["message_text"],
                    app_name=app_name,
                    whatsapp_api_url=config["whatsapp_api_url"],
                    wsp_token=config["wsp_token"]
                )
            except Exception as e:
                logging.error(f"Error processing message {msg_data['message_id']}: {e}", exc_info=True)

async def process_incoming_webhook_payload(body: dict, app_name_env_var: str, facebook_app_env_var: str) -> None:
    """
    Core logic to process incoming webhook events from WhatsApp.
    Uses structured processing with domain models for better maintainability.
    
    Args:
        body: WhatsApp webhook payload
        app_name_env_var: Environment variable name for app name
        facebook_app_env_var: Environment variable name for Facebook app URL
    """
    # Validate configuration
    config = _validate_webhook_config(app_name_env_var, facebook_app_env_var)
    if not config:
        return

    app_name = config["app_name"]
    logging.info(f"Processing incoming webhook for app: {app_name}")

    # Parse webhook payload using Pydantic model
    webhook_payload = parse_webhook_payload(body)
    if not webhook_payload:
        logging.error(f"Failed to parse webhook payload for app {app_name}")
        # Try legacy processing as fallback
        await _process_webhook_legacy(body, config)
        return

    # Extract text messages using the domain model
    text_messages = webhook_payload.get_text_messages()
    
    if not text_messages:
        logging.info(f"No text messages found in webhook payload for app {app_name}")
        return

    # Process each text message
    for sender_wa_id, message in text_messages:
        message_text = message.text.body
        message_id = message.id
        
        logging.info(f"Processing text message (ID: {message_id}) from user {sender_wa_id}, app {app_name}")
        
        try:
            await _process_single_text_message(
                user_wa_id=sender_wa_id,
                message_text=message_text,
                app_name=app_name,
                whatsapp_api_url=config["whatsapp_api_url"],
                wsp_token=config["wsp_token"]
            )
        except Exception as e:
            logging.error(f"Error processing message {message_id} from {sender_wa_id}: {e}", exc_info=True)


async def _process_webhook_legacy(body: dict, config: Dict[str, str]) -> None:
    """
    Legacy webhook processing for backwards compatibility.
    Used as fallback when Pydantic parsing fails.
    
    Args:
        body: Raw webhook payload
        config: Validated configuration dictionary
    """
    app_name = config["app_name"]
    logging.info(f"Using legacy processing for app: {app_name}")

    if 'entry' not in body or not body['entry']:
        logging.info(f"No 'entry' in body for app {app_name}")
        return

    # Process each entry
    for entry in body['entry']:
        try:
            await _process_webhook_entry(entry, config)
        except Exception as e:
            entry_id = entry.get('id', 'N/A')
            logging.error(f"Error processing entry {entry_id}: {e}", exc_info=True)

async def receive_message_aa(body: dict) -> None:
    """
    Handles incoming messages for Estandar AA application.
    
    Args:
        body: WhatsApp webhook payload dictionary
    """
    logger = get_logger("webhook_aa")
    logger.info("Processing AA webhook request")
    
    await process_incoming_webhook_payload(
        body=body,
        app_name_env_var="ESTANDAR_AA_APP_NAME",
        facebook_app_env_var="ESTANDAR_AA_FACEBOOK_APP"
    )


async def receive_message_pp(body: dict) -> None:
    """
    Handles incoming messages for Estandar PP application.
    
    Args:
        body: WhatsApp webhook payload dictionary
    """
    logger = get_logger("webhook_pp")
    logger.info("Processing PP webhook request")
    
    await process_incoming_webhook_payload(
        body=body,
        app_name_env_var="ESTANDAR_PP_APP_NAME",
        facebook_app_env_var="ESTANDAR_PP_FACEBOOK_APP"
    )