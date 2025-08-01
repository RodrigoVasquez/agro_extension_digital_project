"""
Agent service client utilities for communication with the AI agent service.
"""
import httpx
import json
import logging
from typing import Any, Optional
from ..auth.google_auth import get_id_token


async def send_to_agent(
    app_name: str,
    user_id: str,
    session_id: str,
    message: str,
    agent_url: Optional[str] = None
) -> dict[str, Any]:
    """
    Envía mensaje al agente usando httpx - simple y directo.
    
    Args:
        app_name: Nombre de la aplicación (AA, PP, etc.)
        user_id: ID del usuario de WhatsApp
        session_id: ID de la sesión
        message: Mensaje del usuario
        agent_url: URL del agente (opcional, usa APP_URL por defecto)
        
    Returns:
        dict: Respuesta del agente con la información procesada
        
    Raises:
        httpx.HTTPError: Si la comunicación con el agente falla
        json.JSONDecodeError: Si la respuesta no es JSON válido
    """
    import os
    agent_url = agent_url or os.getenv("APP_URL")
    
    if not agent_url:
        raise ValueError("Agent URL not configured (APP_URL environment variable)")
    
    payload = {
        "app_name": app_name,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": message}]
        },
        "streaming": False
    }
    
    # Obtener token usando función existente
    id_token = await get_id_token(agent_url)
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    logging.info(f"Sending message to agent for app {app_name}, user {user_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{agent_url}/run",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        
        response_data = response.json()
        
        # Extraer texto de la respuesta del agente
        if isinstance(response_data, list) and response_data:
            last_event = response_data[-1]
            content = last_event.get("content")
            if content:
                parts = content.get("parts")
                if isinstance(parts, list) and parts:
                    first_part = parts[0]
                    if isinstance(first_part, dict) and "text" in first_part:
                        return {
                            "response": first_part["text"].strip(),
                            "raw_response": response_data
                        }
        
        logging.warning(f"Unexpected response format from agent: {response_data}")
        return {
            "response": "Error: No se pudo extraer el texto de la respuesta del agente.",
            "raw_response": response_data
        }


def extract_agent_response_text(response_data: Any) -> str:
    """
    Extrae el texto de respuesta de la estructura del agente.
    
    Args:
        response_data: Datos crudos de respuesta del agente
        
    Returns:
        str: Texto extraído o mensaje de error
    """
    try:
        if isinstance(response_data, list) and response_data:
            last_event = response_data[-1]
            content = last_event.get("content")
            if content:
                parts = content.get("parts")
                if isinstance(parts, list) and parts:
                    first_part = parts[0]
                    if isinstance(first_part, dict) and "text" in first_part:
                        return first_part["text"].strip()
        
        logging.warning(f"Could not extract text from agent response: {response_data}")
        return "Error: No se pudo extraer el texto de la respuesta del agente."
        
    except Exception as e:
        logging.error(f"Error extracting agent response text: {e}")
        return "Error: Error inesperado al procesar la respuesta del agente."
