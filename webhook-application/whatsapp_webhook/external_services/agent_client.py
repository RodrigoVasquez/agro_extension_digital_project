"""
Agent service client utilities for communication with the AI agent service.
"""
import httpx
import logging
from typing import Any, Optional

from ..auth.google_auth import get_id_token
from ..utils.app_config import config


async def send_to_agent(
    app_name: str,
    user_id: str,
    session_id: str,
    message: str,
) -> dict[str, Any]:
    """
    Sends a message to the agent service.
    """
    if not config.agent.url:
        raise ValueError("Agent URL is not configured.")

    payload = {
        "app_name": app_name,
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

    logging.info(f"Sending message to agent for app {app_name}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{config.agent.url}/run", json=payload, headers=headers)
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
