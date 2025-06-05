import requests
import os
import json
from whatsapp_webhook.utils import idtoken_from_metadata_server

APP_URL=os.getenv("APP_URL")  # Default to localhost if not set

def create_session(user: str, app_name: str,session_id: str):
    token = idtoken_from_metadata_server(APP_URL)
    session_url = f"{APP_URL}/apps/{app_name}/users/{user}/sessions/{session_id}"

    # Encabezados
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Cuerpo de la solicitud
    payload = {
        "state": {
            "preferred_language": "Spanish",
            "visit_count": 5
        }
    }

    # Realizar la solicitud POST
    response = requests.post(session_url, headers=headers, json=payload)