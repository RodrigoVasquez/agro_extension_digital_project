import requests
import os
import json
import re # Not strictly needed for the new send_message but kept for now
import logging
from .utils import idtoken_from_metadata_server # Relative import
from .sessions import create_session # Relative import

APP_URL = os.getenv("APP_URL")

def send_message(user: str, app_name: str, session_id: str, message: str):
    """
    Sends a message to the internal agent service and parses the response.
    The agent service is expected to return a JSON array, where the last element
    contains the text response.
    """
    if not APP_URL:
        logging.error("APP_URL environment variable is not set. Cannot send message to agent.")
        return "Error: Servicio de agente no configurado (URL)."

    try:
        logging.info(f"Fetching ID token for {APP_URL} to send message for app {app_name}, user {user}")
        id_token = idtoken_from_metadata_server(APP_URL)
        logging.info(f"ID token fetched successfully for app {app_name}, user {user}.")
    except Exception as e:
        logging.exception(f"Error generating ID token for {APP_URL} (app {app_name}, user {user}): {e}")
        return "Error: No se pudo autenticar con el servicio del agente. Por favor contacte al administrador."

    session_url = f"{APP_URL}/run" # Corrected endpoint

    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "app_name": app_name,
        "user_id": user,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": message}]
        },
        "streaming": False,
    }

    logging.info(f"Sending message to agent for app {app_name}, user {user}. Payload: {json.dumps(payload)}")
    try:
        response = requests.post(session_url, headers=headers, json=payload)
        response.raise_for_status()
        
        logging.debug(f"Raw response from agent for app {app_name}, user {user}: {response.text}")
        response_data = response.json()

        if isinstance(response_data, list) and response_data:
            last_event = response_data[-1]
            content = last_event.get("content")
            if content:
                parts = content.get("parts")
                if isinstance(parts, list) and parts:
                    first_part = parts[0]
                    if isinstance(first_part, dict) and "text" in first_part:
                        final_text = first_part["text"]
                        logging.info(f"Successfully extracted text for app {app_name}, user {user}: {final_text}")
                        return final_text.strip()
            
            logging.warning(f"Could not find \'text\' in the expected structure of the last event for app {app_name}, user {user}: {last_event}")
            return "Error: No se pudo extraer el texto de la respuesta del agente."
        else:
            logging.warning(f"Response data is not a list or is empty for app {app_name}, user {user}: {response.text}")
            return "Error: Formato de respuesta inesperado del agente."
            
    except json.JSONDecodeError:
        logging.exception(f"Failed to decode JSON response from agent for app {app_name}, user {user}: {response.text}")
        return "Error: La respuesta del agente no es un JSON válido."
    except requests.exceptions.RequestException as e:
        logging.exception(f"Request to agent failed for app {app_name}, user {user}: {e}")
        return "Error: Fallo la comunicación con el servicio del agente."
    except Exception as e:
        logging.exception(f"An unexpected error occurred while parsing agent response for app {app_name}, user {user}: {e}")
        return "Error: Error inesperado al procesar la respuesta del agente."

async def _process_single_text_message(user_wa_id: str, message_text: str, app_name: str, whatsapp_api_url: str, wsp_token: str):
    """
    Processes a single text message: creates a session, gets a response from the internal service,
    and sends it back to the user via WhatsApp API.
    """
    logging.info(f"Processing text message from user {user_wa_id} for app {app_name}: '{message_text}'")
    
    create_session(user_wa_id, app_name, user_wa_id) # session_id is user_wa_id
    
    response_from_service = send_message(user_wa_id, app_name, user_wa_id, message_text)
    
    whatsapp_payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": user_wa_id,
        "type": "text",
        "text": {
            "body": response_from_service
        }
    }
    headers = {
        "Authorization": f"Bearer {wsp_token}",
        "Content-Type": "application/json"
    }
    
    logging.info(f"Sending response to WhatsApp for user {user_wa_id}, app {app_name}. Payload: {json.dumps(whatsapp_payload)}")
    try:
        resp = requests.post(whatsapp_api_url, headers=headers, data=json.dumps(whatsapp_payload))
        logging.info(f"Response from WhatsApp API for user {user_wa_id}, app {app_name}: Status {resp.status_code} - Text: {resp.text}")
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        logging.exception(f"Error posting to WhatsApp API for user {user_wa_id}, app {app_name}")
    except Exception:
        logging.exception(f"Unexpected error sending message to WhatsApp API for user {user_wa_id}, app {app_name}")

async def process_incoming_webhook_payload(body: dict, app_name_env_var: str, facebook_app_env_var: str):
    """
    Core logic to process incoming webhook events from WhatsApp.
    Iterates through messages and calls _process_single_text_message for text messages.
    """
    app_name = os.getenv(app_name_env_var)
    whatsapp_api_url = os.getenv(facebook_app_env_var)
    wsp_token = os.getenv("WSP_TOKEN")

    if not app_name:
        logging.error(f"Environment variable {app_name_env_var} not set. Cannot process webhook.")
        return
    if not whatsapp_api_url:
        logging.error(f"Environment variable {facebook_app_env_var} not set. Cannot process webhook.")
        return
    if not wsp_token:
        logging.error("Environment variable WSP_TOKEN not set. Cannot process webhook.")
        return

    logging.info(f"Processing incoming webhook for app: {app_name} using URL: {whatsapp_api_url}")

    if 'entry' in body and body['entry']:
        for entry in body['entry']:
            entry_id = entry.get('id', 'N/A')
            logging.debug(f"Processing entry ID: {entry_id} for app {app_name}")
            if 'changes' in entry and entry['changes']:
                for change in entry['changes']:
                    field = change.get('field', 'N/A')
                    logging.debug(f"Processing change field: {field} in entry {entry_id} for app {app_name}")
                    if field == 'messages':
                        value = change.get('value', {})
                        
                        user_wa_id = None
                        if 'contacts' in value and isinstance(value['contacts'], list) and value['contacts']:
                            user_wa_id = value['contacts'][0].get('wa_id')

                        if not user_wa_id:
                            logging.warning(f"No wa_id found in contacts for change value in entry {entry_id}, app {app_name}. Value: {value}")
                            continue

                        if 'messages' in value and isinstance(value['messages'], list):
                            for message_obj in value['messages']:
                                message_id = message_obj.get('id', 'N/A')
                                if message_obj.get('type') == 'text':
                                    message_text_data = message_obj.get('text', {})
                                    message_text = message_text_data.get('body')

                                    if not message_text:
                                        logging.warning(f"No text body in message_obj (ID: {message_id}) for user {user_wa_id}, app {app_name}. Message: {message_obj}")
                                        continue
                                    
                                    await _process_single_text_message(user_wa_id, message_text, app_name, whatsapp_api_url, wsp_token)
                                else:
                                    logging.info(f"Skipping non-text message (ID: {message_id}, Type: {message_obj.get('type')}) for user {user_wa_id}, app {app_name}.")
                        else:
                            logging.warning(f"No 'messages' array in 'value' or not a list for user {user_wa_id}, app {app_name}, entry {entry_id}. Value: {value}")
            else:
                logging.debug(f"No 'changes' in entry {entry_id} for app {app_name}.")
    else:
        logging.info(f"No 'entry' in body or body['entry'] is empty for app {app_name}. Body: {body}")

async def receive_message_aa(body: dict):
    """Handles messages for Estandar AA"""
    logging.info("receive_message_aa invoked")
    await process_incoming_webhook_payload(
        body,
        app_name_env_var="ESTANDAR_AA_APP_NAME",
        facebook_app_env_var="ESTANDAR_AA_FACEBOOK_APP"
    )

async def receive_message_pp(body: dict):
    """Handles messages for Estandar PP"""
    logging.info("receive_message_pp invoked")
    await process_incoming_webhook_payload(
        body,
        app_name_env_var="ESTANDAR_PP_APP_NAME",
        facebook_app_env_var="ESTANDAR_PP_FACEBOOK_APP"
    )