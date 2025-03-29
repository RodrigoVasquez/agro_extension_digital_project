from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import json

app = FastAPI()


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
            "Authorization": "Bearer EAAeFypiAzZAsBO6ArO4yBNpgYyE1CcK3bSxX1PZBEcn8TPGcrfSZAUKmWfhnOR60CrdDQHZAaLiWiEuPpsDIWIGKZCIOrrhxECr3S1F3U2hpb8FLbbyUoY3jOzNm658BK74Y0PQeuV7vCrfvAHS2sp519q6oZBPIU4gzK0UXRpIuisGdF0ZBXrFN7UUtEt6D7nbUgrvoHU5AJxm3j0xrT0haJZC4",
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
                        print("Received message:", value)
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
