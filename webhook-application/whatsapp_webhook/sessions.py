import requests
import os
import json
from .auth.google_auth import idtoken_from_metadata_server
from .utils.logging import get_logger

APP_URL = os.getenv("APP_URL")  # Default to localhost if not set

def create_session(user: str, app_name: str, session_id: str):
    """
    Creates a session for the user in the agent service.
    
    Args:
        user: User WhatsApp ID
        app_name: Application name (AA, PP, etc.)
        session_id: Session identifier
    """
    logger = get_logger("sessions", {"app_name": app_name})
    
    try:
        token = idtoken_from_metadata_server(APP_URL)
        session_url = f"{APP_URL}/apps/{app_name}/users/{user}/sessions/{session_id}"

        # Headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Request body
        payload = {
            "state": {
                "preferred_language": "Spanish",
                "visit_count": 5
            }
        }

        logger.info(f"Creating session for user", extra={"user_id": user, "session_id": session_id})
        
        # Make POST request
        response = requests.post(session_url, headers=headers, json=payload)
        response.raise_for_status()
        
        logger.info("Session created successfully", extra={"user_id": user, "session_id": session_id})
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create session: {e}", extra={"user_id": user, "session_id": session_id}, exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating session: {e}", extra={"user_id": user, "session_id": session_id}, exc_info=True)
        raise