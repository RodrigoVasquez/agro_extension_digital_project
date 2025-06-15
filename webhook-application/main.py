from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import os
import uvicorn
import logging

from whatsapp_webhook.messages import receive_message_aa, receive_message_pp 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

@app.get("/estandar_aa_webhook")
async def verify_aa_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    verify_token_env = os.getenv("VERIFY_TOKEN_AA", os.getenv("VERIFY_TOKEN")) # Specific or fallback

    logging.info(f"AA Webhook verification attempt. Mode: {mode}, Token: {token}, Challenge: {challenge}")

    if mode == "subscribe" and token == verify_token_env:
        logging.info(f"AA Webhook verified successfully. Challenge: {challenge}")
        return JSONResponse(content=int(challenge))
    else:
        logging.warning(f"AA Webhook verification failed. Mode: {mode}, Token: {token} (Expected: {verify_token_env})")
        return JSONResponse(content="Forbidden", status_code=403)

@app.get("/estandar_pp_webhook")
async def verify_pp_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    verify_token_env = os.getenv("VERIFY_TOKEN_PP", os.getenv("VERIFY_TOKEN")) # Specific or fallback

    logging.info(f"PP Webhook verification attempt. Mode: {mode}, Token: {token}, Challenge: {challenge}")

    if mode == "subscribe" and token == verify_token_env:
        logging.info(f"PP Webhook verified successfully. Challenge: {challenge}")
        return JSONResponse(content=int(challenge))
    else:
        logging.warning(f"PP Webhook verification failed. Mode: {mode}, Token: {token} (Expected: {verify_token_env})")
        return JSONResponse(content="Forbidden", status_code=403)

@app.post("/estandar_aa_webhook")
async def handle_estandar_aa_webhook(request: Request):
    logging.info("Received POST request on /estandar_aa_webhook")
    try:
        body = await request.json()
        logging.debug(f"AA Webhook request body: {json.dumps(body)}")
        await receive_message_aa(body) # Call the refactored logic
        logging.info("Finished processing AA webhook. Returning 200 OK to WhatsApp.")
        # WhatsApp expects a 200 OK quickly. The actual processing happens in receive_message_aa.
        return JSONResponse(content={"status": "ok"}, status_code=200)
    except json.JSONDecodeError:
        logging.exception("Failed to decode JSON from AA webhook request.")
        return JSONResponse(content={"status": "error", "message": "Invalid JSON format"}, status_code=400)
    except Exception as e:
        logging.exception("An unexpected error occurred in handle_estandar_aa_webhook")
        # Still return 200 OK to WhatsApp to prevent retries for errors during our processing
        return JSONResponse(content={"status": "ok"}, status_code=200)

@app.post("/estandar_pp_webhook")
async def handle_estandar_pp_webhook(request: Request):
    logging.info("Received POST request on /estandar_pp_webhook")
    try:
        body = await request.json()
        logging.debug(f"PP Webhook request body: {json.dumps(body)}")
        await receive_message_pp(body) # Call the refactored logic for PP
        logging.info("Finished processing PP webhook. Returning 200 OK to WhatsApp.")
        return JSONResponse(content={"status": "ok"}, status_code=200)
    except json.JSONDecodeError:
        logging.exception("Failed to decode JSON from PP webhook request.")
        return JSONResponse(content={"status": "error", "message": "Invalid JSON format"}, status_code=400)
    except Exception as e:
        logging.exception("An unexpected error occurred in handle_estandar_pp_webhook")
        return JSONResponse(content={"status": "ok"}, status_code=200)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"Starting Uvicorn server on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)