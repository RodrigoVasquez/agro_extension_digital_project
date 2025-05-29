import requests
import os
import json

APP_URL=os.getenv("APP_URL")  # Default to localhost if not set

def send_message(user: str, session_id: str, message: str):
    token = "your_token_here"
    session_url = f"{APP_URL}/run_sse"

    # Encabezados
    headers = {
   #     "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Cuerpo de la solicitud
    payload = {
        "app_name": "agent",
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

    if response.text.startswith('data: '):
        json_data = response.text[6:]  # Quitar 'data: '

# Convertir la cadena JSON a un diccionario de Python
    parsed_data = json.loads(json_data)
    return parsed_data['content']['parts'][0]['text']
