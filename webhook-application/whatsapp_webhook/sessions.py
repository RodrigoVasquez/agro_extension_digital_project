import requests
import os
import json
from .auth.google_auth import idtoken_from_metadata_server
from .utils.logging import get_logger
from .utils.app_config import config, AppType, WhatsAppConfig

def _session_exists(user: str, whatsapp_config: WhatsAppConfig, session_id: str, headers: dict) -> bool:
    """
    Check if a session already exists for the user.
    
    Args:
        user: User WhatsApp ID
        whatsapp_config: WhatsApp configuration containing agent info
        session_id: Session identifier
        headers: Request headers with authorization
        
    Returns:
        True if session exists, False otherwise
    """
    try:
        check_url = whatsapp_config.get_agent_session_url(user, session_id)
        if not check_url:
            return False
            
        response = requests.get(check_url, headers=headers)
        
        # If we get a 200 response, the session exists
        if response.status_code == 200:
            return True
        # If we get a 404, the session doesn't exist
        elif response.status_code == 404:
            return False
        else:
            # For other status codes, log and assume session doesn't exist
            response.raise_for_status()
            return False
            
    except requests.exceptions.RequestException:
        # If there's an error checking, assume session doesn't exist and let create handle it
        return False

def create_session(user: str, app_name: str, session_id: str):
    """
    Creates a session for the user in the agent service if it doesn't already exist.
    
    Args:
        user: User WhatsApp ID
        app_name: Application name (AA, PP, etc.)
        session_id: Session identifier
        
    Returns:
        Session data from the API response
    """
    logger = get_logger("sessions", {"app_name": app_name})
    
    # Mapear nombre de app a nombre esperado por el agente
    app_type = AppType.AA if app_name == "AA" else AppType.PP
    whatsapp_config = config.get_whatsapp_config(app_type)
    
    try:
        token = idtoken_from_metadata_server(config.agent.url)
        
        # Headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Check if session already exists
        if _session_exists(user, whatsapp_config, session_id, headers):
            logger.info("Session already exists, skipping creation", extra={
                "user_id": user, 
                "session_id": session_id,
                "agent_app_name": whatsapp_config.agent_app_name
            })
            # Get existing session data
            get_url = whatsapp_config.get_agent_session_url(user, session_id)
            if get_url:
                response = requests.get(get_url, headers=headers)
            response.raise_for_status()
            return response.json()

        # Session doesn't exist, create it
        session_url = f"adk"

        # Request body
        payload = {
            "state": {
                "preferred_language": "Spanish",
                "visit_count": 5
            }
        }

        logger.info(f"Creating new session for user", extra={
            "user_id": user, 
            "session_id": session_id,
            "agent_app_name": whatsapp_config.agent_app_name,
            "session_url": session_url
        })
        
        # Make POST request to create session
        create_url = whatsapp_config.get_agent_session_url(user, session_id)
        if create_url:
            response = requests.post(create_url, headers=headers, json=payload)
            response.raise_for_status()
        
            logger.info("Session created successfully", extra={"user_id": user, "session_id": session_id})
            return response.json()
        else:
            raise ValueError("Could not generate session URL")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create session: {e}", extra={"user_id": user, "session_id": session_id}, exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating session: {e}", extra={"user_id": user, "session_id": session_id}, exc_info=True)
        raise
        raise