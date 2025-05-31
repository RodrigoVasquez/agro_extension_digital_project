import requests
import os
import json
import re
from whatsapp_webhook.utils import idtoken_from_metadata_server

APP_URL=os.getenv("APP_URL")  # Default to localhost if not set

def send_message(user: str, app_name: str,session_id: str, message: str):
    try:
        print("Fetching ID token...")
        id_token = idtoken_from_metadata_server(APP_URL)
        print("ID token fetched successfully.")
    except Exception as e:
        print(f"Error generating ID token: {e}")
        return "Error: Could not authenticate to the agent service. Please contact administrator."

    session_url = f"{APP_URL}/run_sse"

    # Encabezados
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }

    # Cuerpo de la solicitud
    payload = {
        "app_name": app_name,
        "user_id": user,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{
            "text": message
             }]
        },
        "streaming": False,
     }
    # Realizar la solicitud POST
    response = requests.post(session_url, headers=headers, json=payload)

    json_blocks = re.findall(r'data:\s*(\{.*?\})(?=\n|$)', response.text, re.DOTALL)

# Obtener el texto del último bloque
    if json_blocks:
        last_json = json.loads(json_blocks[-1])
        parts = last_json.get("content", {}).get("parts", [])
        if parts and "text" in parts[0]:
            final_text = parts[0]["text"]
            return final_text.strip()
        else:
            return "Error en la respuesta del agente contactar al administrador."
    else:
        return "Error en la respuesta del agente contactar al administrador."