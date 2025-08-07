"""
Agent service client utilities for communication with the AI agent service.
"""
import httpx
import logging
from typing import Any, Optional

from ..auth.google_auth import get_id_token
from ..utils.app_config import config, WhatsAppConfig, AppType


async def send_to_agent(
    whatsapp_config: WhatsAppConfig,
    user_id: str,
    session_id: str,
    message: str,
) -> dict[str, Any]:
    """
    Sends a message to the agent service.
    """
    if not config.agent.url:
        raise ValueError("Agent URL is not configured.")

    # Get the complete agent run URL
    agent_run_url = whatsapp_config.get_agent_run_url()
    if not agent_run_url:
        raise ValueError("Agent run URL is not configured.")

    payload = {
        "app_name": whatsapp_config.agent_app_name,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {"role": "user", "parts": [{"text": message}]},
        "streaming": False,
    }

    id_token = await get_id_token(config.agent.url)
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json",
    }

    logging.info(f"Sending message to agent for app {whatsapp_config.agent_app_name}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(agent_run_url, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        if isinstance(response_data, list) and response_data:
            last_event = response_data[-1]
            if content := last_event.get("content"):
                if parts := content.get("parts"):
                    if isinstance(parts, list) and parts and "text" in parts[0]:
                        return {"response": parts[0]["text"].strip(), "raw_response": response_data}

        logging.warning(f"Unexpected response format from agent: {response_data}")
        return {"response": "Error: Could not extract text from agent response.", "raw_response": response_data}


async def _session_exists(
    user_id: str,
    whatsapp_config: WhatsAppConfig,
    session_id: str,
    headers: dict
) -> bool:
    """
    Check if a session already exists for the user.
    """
    try:
        check_url = whatsapp_config.get_agent_session_url(user_id, session_id)
        if not check_url:
            logging.error(f"Could not generate session check URL for user {user_id}")
            return False
        
        logging.debug(f"Checking if session exists for user {user_id}, session {session_id}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(check_url, headers=headers)
            
            # If we get a 200 response, the session exists
            if response.status_code == 200:
                logging.info(f"Session exists for user {user_id}")
                return True
            # If we get a 404, the session doesn't exist
            elif response.status_code == 404:
                logging.info(f"Session does not exist for user {user_id}")
                return False
            else:
                # For other status codes, log and assume session doesn't exist
                logging.warning(f"Unexpected status code {response.status_code} from session check for user {user_id}")
                response.raise_for_status()
                return False
                
    except Exception as e:
        # If there's an error checking, assume session doesn't exist and let create handle it
        logging.error(f"Error checking session for user {user_id}: {e}", exc_info=True)
        return False


async def create_agent_session(user_id: str, app_name: str, session_id: str) -> dict[str, Any]:
    """
    Creates a session for the user in the agent service if it doesn't already exist.
    
    Args:
        user_id: User WhatsApp ID
        app_name: Application name (AA, PP, etc.)
        session_id: Session identifier
        
    Returns:
        Session data from the API response
    """
    if not config.agent.url:
        raise ValueError("Agent URL is not configured.")
    
    logging.info(f"Starting session creation process for user {user_id}")
    
    # Map app name to app type
    app_type = AppType.AA if app_name == "AA" else AppType.PP
    whatsapp_config = config.get_whatsapp_config(app_type)
    
    logging.debug(f"Agent configuration loaded for app {whatsapp_config.agent_app_name}")
    
    try:
        id_token = await get_id_token(config.agent.url)
        headers = {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json"
        }
        
        # Check if session already exists
        if await _session_exists(user_id, whatsapp_config, session_id, headers):
            logging.info(f"Session already exists for user {user_id}, skipping creation")
            # Get existing session data
            get_url = whatsapp_config.get_agent_session_url(user_id, session_id)
            if get_url:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(get_url, headers=headers)
                    response.raise_for_status()
                    return response.json()
            else:
                raise ValueError("Could not generate session URL for existing session")

        # Session doesn't exist, create it
        payload = {
            "state": {
                "preferred_language": "Spanish",
                "visit_count": 5
            }
        }

        logging.info(f"Creating new session for user {user_id}")
        
        # Make POST request to create session
        create_url = whatsapp_config.get_agent_session_url(user_id, session_id)
        if create_url:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(create_url, headers=headers, json=payload)
                response.raise_for_status()
                
                logging.info(f"Session created successfully for user {user_id}")
                return response.json()
        else:
            raise ValueError("Could not generate session creation URL")
        
    except Exception as e:
        logging.error(f"Error during session creation for user {user_id}: {e}", exc_info=True)
        raise
