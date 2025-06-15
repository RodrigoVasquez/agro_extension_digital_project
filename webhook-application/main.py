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
                    "body": "Hello from Python!" # Default, will be overwritten
                }
        }
        if 'entry' in body and body['entry']:
            for entry in body['entry']:
                logging.info(f"Processing entry ID: {entry.get('id', 'N/A')}")
                if 'changes' in entry and entry['changes']:
                    for change in entry['changes']:
                        logging.info(f"Processing change field: {change.get('field', 'N/A')}")
                        if change.get('field') == 'messages':
                            value = change.get('value', {})
                            
                            user_wa_id = None
                            if 'contacts' in value and isinstance(value['contacts'], list) and value['contacts']:
                                user_wa_id = value['contacts'][0].get('wa_id')

                            if not user_wa_id:
                                logging.warning(f"No wa_id found in contacts for change value: {value}")
                                continue # Move to the next change if no user_wa_id

                            if 'messages' in value and isinstance(value['messages'], list):
                                for message_obj in value['messages']: # Iterate through each message in the 'messages' array
                                    if message_obj.get('type') == 'text':
                                        message_text_data = message_obj.get('text', {})
                                        message_text = message_text_data.get('body')

                                        if not message_text:
                                            logging.warning(f"No text body in message_obj: {message_obj} for user {user_wa_id}")
                                            continue # Move to the next message_obj

                                        logging.info(f"Processing text message from user {user_wa_id}: '{message_text}'")
                                        
                                        logging.info(f"Creating session for user: {user_wa_id}, app: {os.getenv('ESTANDAR_AA_APP_NAME')}")
                                        create_session(user_wa_id, os.getenv("ESTANDAR_AA_APP_NAME"), user_wa_id)
                                        
                                        logging.info(f"Sending message to internal service for user {user_wa_id}")
                                        response_from_service = send_message(user_wa_id, os.getenv("ESTANDAR_AA_APP_NAME"), user_wa_id, message_text)
                                        logging.info(f"Response from internal send_message: {response_from_service}")
                                        
                                        payload['text']['body'] = response_from_service
                                        payload['to'] = user_wa_id
                                        
                                        logging.info(f"Payload to WhatsApp API: {json.dumps(payload, indent=2)}")
                                        try:
                                            resp = requests.post(url, headers=headers, data=json.dumps(payload))
                                            logging.info(f"Response from WhatsApp API: Status {resp.status_code} - Text: {resp.text}")
                                            resp.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                                        except requests.exceptions.RequestException as post_exc:
                                            logging.exception(f"Error posting to WhatsApp API for user {user_wa_id}")
                                    else:
                                        logging.info(f"Skipping non-text message (type: {message_obj.get('type')}) for user {user_wa_id}.")
                            else:
                                logging.warning(f"No 'messages' array in 'value' or not a list for user {user_wa_id}. Value: {value}")
                        # Removed premature return that was here
                # Removed premature return that was here
        # This 'else' corresponds to the 'for entry in body['entry']:' loop.
        # It executes if the loop completes normally (all entries processed) or if 'body['entry']' was empty.
        logging.info("Finished processing all entries/changes or no entries were present. Returning 200 OK.")
        return JSONResponse(content={"status": "ok"}, status_code=200)
    except Exception as e:
        logging.exception("An unexpected error occurred in receive_message")
        # Always return 200 OK to WhatsApp to acknowledge receipt and prevent retries,
        # even if internal processing failed. The error is logged for debugging.
        return JSONResponse(content={"status": "ok"}, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))