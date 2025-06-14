from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import json
import uuid
import os
import uvicorn
import logging

from whatsapp_webhook.messages import send_message
from whatsapp_webhook.sessions import create_session
from whatsapp_webhook.utils import idtoken_from_metadata_server

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.info(f"Webhook verified successfully. Challenge: {challenge}")
        return JSONResponse(content=int(challenge))
    logging.warning(f"Webhook verification failed. Mode: {mode}, Token: {token}")
    return JSONResponse(content="Forbidden", status_code=403)

@app.post("/estandar_aa_webhook")
async def receive_message(request: Request):
    try:
        body = await request.json()
        logging.info(f"Received request body: {json.dumps(body, indent=2)}")
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
            logging.info(f"Processing entry ID: {entry.get('id', 'N/A')}")
            for change in entry['changes']:
                logging.info(f"Processing change field: {change.get('field', 'N/A')}")
            # Handle different types of changes (e.g., messages, status)
                if change['field'] == 'messages':
                # Extract message details
                    value = change['value']
                    # Process the incoming message
                    if value['messages'][0]['type'] == 'text':
                        user = value['contacts'][0]['wa_id']
                        message_text = value['messages'][0]['text']['body']
                        logging.info(f"Processing text message from user {user}: '{message_text}'")
                        
                        logging.info(f"Creating session for user: {user}, app: {os.getenv('ESTANDAR_AA_APP_NAME')}")
                        create_session(user, os.getenv("ESTANDAR_AA_APP_NAME"), user)
                        
                        logging.info(f"Sending message to internal service for user {user}")
                        response = send_message(user, os.getenv("ESTANDAR_AA_APP_NAME"), user, message_text)
                        logging.info(f"Response from internal send_message: {response}")
                        
                        payload['text']['body'] = response
                        payload['to'] = value['contacts'][0]['wa_id']
                        
                        logging.info(f"Payload to WhatsApp API: {json.dumps(payload, indent=2)}")
                        try:
                            resp = requests.post(url, headers=headers, data=json.dumps(payload))
                            logging.info(f"Response from WhatsApp API: Status {resp.status_code} - Text: {resp.text}")
                            resp.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                        except requests.exceptions.RequestException as post_exc:
                            logging.exception("Error posting to WhatsApp API")
                    logging.info("Returning 200 OK after processing message.")
                    return JSONResponse(content={"status": "ok"}, status_code=200)
            logging.info("Returning 200 OK after processing entry changes.")
            return JSONResponse(content={"status": "ok"}, status_code=200)
        else:
            logging.info("No entries found in the request body or loop completed. Returning 200 OK.")
            return JSONResponse(content={"status": "ok"}, status_code=200)
    except Exception as e:
        logging.exception("An unexpected error occurred in receive_message")
        return JSONResponse(content={"status": "ok"}, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))