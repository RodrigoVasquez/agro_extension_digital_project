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
    agent_name: Optional[str] = None,
) -> dict[str, Any]:
    """Sends a message to the agent service."""
    if not config.agent.url:
        raise ValueError("Agent URL is not configured.")

    agent_run_url = whatsapp_config.get_agent_run_url()
    if not agent_run_url:
        raise ValueError("Agent run URL is not configured.")

    target_agent_name = agent_name or whatsapp_config.agent_app_name

    payload = {
        "app_name": target_agent_name,
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

    logging.info(f"Sending message to agent {target_agent_name} for user {user_id}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(agent_run_url, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        if isinstance(response_data, list) and response_data:
            if content := response_data[-1].get("content"):
                if parts := content.get("parts"):
                    if isinstance(parts, list) and parts and "text" in parts[0]:
                        return {"response": parts[0]["text"].strip(), "raw_response": response_data}

        logging.warning(f"Unexpected response format from agent: {response_data}")
        return {"response": "Error: Could not extract text from agent response.", "raw_response": response_data}

async def create_agent_session(user_id: str, app_type: AppType, session_id: str, agent_name: Optional[str] = None) -> dict[str, Any]:
    """Creates a session for the user in the agent service if it doesn't already exist."""
    if not config.agent.url:
        raise ValueError("Agent URL is not configured.")

    whatsapp_config = config.get_whatsapp_config(app_type)
    target_agent_name = agent_name or whatsapp_config.agent_app_name
    session_url = whatsapp_config.get_agent_session_url(user_id, session_id, target_agent_name)

    if not session_url:
        raise ValueError("Could not generate session URL.")

    id_token = await get_id_token(config.agent.url)
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(session_url, headers=headers)
        if response.status_code == 200:
            logging.info(f"Session already exists for user {user_id} with agent {target_agent_name}")
            return response.json()
        elif response.status_code != 404:
            response.raise_for_status()

        logging.info(f"Creating new session for user {user_id} with agent {target_agent_name}")
        payload = {"state": {"preferred_language": "Spanish", "visit_count": 5}}
        response = await client.post(session_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
