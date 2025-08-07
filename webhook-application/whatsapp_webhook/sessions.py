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
            logger = get_logger("session_check")
            logger.error("Could not generate session check URL", extra={
                "user_id": user,
                "session_id": session_id,
                "agent_app_name": whatsapp_config.agent_app_name
            })
            return False
        
        logger = get_logger("session_check")
        logger.debug("Checking if session exists", extra={
            "user_id": user,
            "session_id": session_id,
            "check_url": check_url,
            "agent_app_name": whatsapp_config.agent_app_name
        })
            
        response = requests.get(check_url, headers=headers)
        
        logger.debug("Session check response", extra={
            "user_id": user,
            "session_id": session_id,
            "status_code": response.status_code,
            "response_headers": dict(response.headers),
            "agent_app_name": whatsapp_config.agent_app_name
        })
        
        # If we get a 200 response, the session exists
        if response.status_code == 200:
            logger.info("Session exists", extra={
                "user_id": user,
                "session_id": session_id,
                "agent_app_name": whatsapp_config.agent_app_name
            })
            return True
        # If we get a 404, the session doesn't exist
        elif response.status_code == 404:
            logger.info("Session does not exist", extra={
                "user_id": user,
                "session_id": session_id,
                "agent_app_name": whatsapp_config.agent_app_name
            })
            return False
        else:
            # For other status codes, log and assume session doesn't exist
            logger.warning("Unexpected status code from session check", extra={
                "user_id": user,
                "session_id": session_id,
                "status_code": response.status_code,
                "response_text": response.text[:500],
                "agent_app_name": whatsapp_config.agent_app_name
            })
            response.raise_for_status()
            return False
            
    except requests.exceptions.RequestException as e:
        # If there's an error checking, assume session doesn't exist and let create handle it
        logger = get_logger("session_check")
        logger.error("Request exception during session check", extra={
            "user_id": user,
            "session_id": session_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "agent_app_name": whatsapp_config.agent_app_name
        }, exc_info=True)
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
    
    logger.info("Starting session creation process", extra={
        "user_id": user,
        "app_name": app_name,
        "session_id": session_id
    })
    
    # Mapear nombre de app a nombre esperado por el agente
    app_type = AppType.AA if app_name == "AA" else AppType.PP
    whatsapp_config = config.get_whatsapp_config(app_type)
    
    logger.debug("Agent configuration loaded", extra={
        "user_id": user,
        "session_id": session_id,
        "agent_app_name": whatsapp_config.agent_app_name,
        "app_type": app_type.value,
        "base_agent_url": config.agent.url
    })
    
    try:
        logger.debug("Generating ID token", extra={
            "user_id": user,
            "session_id": session_id,
            "target_url": config.agent.url
        })
        
        token = idtoken_from_metadata_server(config.agent.url)
        
        logger.debug("ID token generated successfully", extra={
            "user_id": user,
            "session_id": session_id,
            "token_length": len(token) if token else 0
        })
        
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
                logger.debug("Fetching existing session data", extra={
                    "user_id": user,
                    "session_id": session_id,
                    "get_url": get_url
                })
                response = requests.get(get_url, headers=headers)
                response.raise_for_status()
                
                logger.debug("Existing session data retrieved", extra={
                    "user_id": user,
                    "session_id": session_id,
                    "status_code": response.status_code
                })
                return response.json()
            else:
                logger.error("Could not generate session URL for existing session", extra={
                    "user_id": user,
                    "session_id": session_id,
                    "agent_app_name": whatsapp_config.agent_app_name
                })
                raise ValueError("Could not generate session URL")

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
            logger.info("Creating new session", extra={
                "user_id": user,
                "session_id": session_id,
                "create_url": create_url,
                "payload": payload,
                "agent_app_name": whatsapp_config.agent_app_name
            })
            
            response = requests.post(create_url, headers=headers, json=payload)
            
            logger.debug("Session creation response", extra={
                "user_id": user,
                "session_id": session_id,
                "status_code": response.status_code,
                "response_headers": dict(response.headers),
                "response_text": response.text[:500] if response.text else None
            })
            
            response.raise_for_status()
        
            logger.info("Session created successfully", extra={
                "user_id": user, 
                "session_id": session_id,
                "agent_app_name": whatsapp_config.agent_app_name
            })
            return response.json()
        else:
            logger.error("Could not generate session creation URL", extra={
                "user_id": user,
                "session_id": session_id,
                "agent_app_name": whatsapp_config.agent_app_name
            })
            raise ValueError("Could not generate session URL")
        
    except requests.exceptions.RequestException as e:
        logger.error("HTTP request failed during session creation", extra={
            "user_id": user, 
            "session_id": session_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "agent_app_name": whatsapp_config.agent_app_name,
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            "response_text": getattr(e.response, 'text', None) if hasattr(e, 'response') else None
        }, exc_info=True)
        raise
    except Exception as e:
        logger.error("Unexpected error during session creation", extra={
            "user_id": user, 
            "session_id": session_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "agent_app_name": getattr(whatsapp_config, 'agent_app_name', 'unknown')
        }, exc_info=True)
        raise