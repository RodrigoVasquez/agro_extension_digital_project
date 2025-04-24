from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import json
import uuid


app = FastAPI()

APP_URL = "https://agent-aa-890639421110.us-central1.run.app"

def create_session(user: str, session_id: str):
    token = "your_token_here"
    session_url = f"{APP_URL}/apps/agent/users/{user}/sessions/{session_id}"

    # Encabezados
    headers = {
   #     "Authorization": f"Bearer {token}",
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



processed_messages = []
@app.get("/")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    VERIFY_TOKEN = "your_verify_token"

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return JSONResponse(content=int(challenge))
    return JSONResponse(content="Forbidden", status_code=403)

@app.post("/")
async def receive_message(request: Request):
    try:
        body = await request.json()
        processed_messages.append(body)
        print("Received message:", body)
        url = "https://graph.facebook.com/v22.0/586486637888050/messages"
        headers = {
            "Authorization": "Bearer EAAeFypiAzZAsBO7jvrQ3BevS85ximW2RjAhq2LlufVcMBHs3tl7Lptjmni9DMqoPUQZCONVyadTpkeoeKczdR68IZBqTOCHfmesiwc7mnS6NRKTBMU6pZCqKxF2G2r66KfmHLWFSbKSVtZAqbyqp3A36HB6ZAmYOvr4tXCG0EZCCN9qEJ6TUJegmNepEyOhDCmfuGZAtc8HdZAMllZBDNoWhdNzzVO",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "56968767906",
            "type": "text",
                "text": {
                    "body": "Hello from Python!"
                }
        }
        for entry in body['entry']:
            for change in entry['changes']:
            # Handle different types of changes (e.g., messages, status)
                if change['field'] == 'messages':
                # Extract message details
                    value = change['value']
                    # Process the incoming message
                    print("Received message:", value)

                    if value['messages'][0]['type'] == 'text':
                        session_id =uuid.uuid4().hex
                        user = value['contacts'][0]['wa_id']
                        create_session(user, session_id)
                        response = send_message(user, session_id, value['messages'][0]['text']['body'])
                        print("Received message:", value)
                        print("Sent message:", response)
                        payload['text']['body'] = response
                        payload['to'] = value['contacts'][0]['wa_id']
                        requests.post(url, headers=headers, data=json.dumps(payload))
                    # Example: Respond to the message
                    # You can add your logic here to respond to the user
                    # For example, you can use the value['messages'][0]['text']['body'] to get the message text
                    # and value['contacts'][0]['wa_id'] to get the user's phone number
                    return JSONResponse(content={"status": "ok"}, status_code=200)
            return JSONResponse(content={"status": "ok"}, status_code=200)
        else:
            return JSONResponse(content={"status": "ok"}, status_code=200)
    except Exception as e:
        print("Error:", e)
        return JSONResponse(content={"status": "ok"}, status_code=200)

