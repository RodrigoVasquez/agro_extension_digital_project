from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import json
import uuid
import os
import uvicorn

from whatsapp_webhook.messages import send_message
from whatsapp_webhook.sessions import create_session
from whatsapp_webhook.utils import idtoken_from_metadata_server

app = FastAPI()

APP_URL = os.getenv("APP_URL")  # Default to localhost if not set

processed_messages = []
@app.get("/estandar_aa_webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return JSONResponse(content=int(challenge))
    return JSONResponse(content="Forbidden", status_code=403)

@app.post("/estandar_aa_webhook")
async def receive_message(request: Request):
    try:
        body = await request.json()
        processed_messages.append(body)
        url = os.getenv("ESTANDAR_AA_FACEBOOK_APP")
        headers = {
            "Authorization": f"Bearer {os.getenv('WSP_TOKEN')}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
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
                        user = value['contacts'][0]['wa_id']
                        create_session(user, os.getenv("ESTANDAR_AA_APP_NAME"), user)
                        response = send_message(user, os.getenv("ESTANDAR_AA_APP_NAME"), user, value['messages'][0]['text']['body'])
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

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))