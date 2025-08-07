"""
WhatsApp API client utilities for sending messages and downloading media.
"""
import httpx
import logging
from typing import Any, Dict, Optional

async def send_whatsapp_message(
    to: str,
    message: Dict[str, Any],
    whatsapp_api_url: str,
    token: str
) -> Dict[str, Any]:
    """Sends a message via the WhatsApp API."""
    if not to.startswith("+"):
        to = f"+{to}"
    
    payload = {"messaging_product": "whatsapp", "to": to, **message}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    logging.info(f"Sending WhatsApp message to {to}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{whatsapp_api_url}/messages", json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        logging.info(f"WhatsApp message sent successfully: {result}")
        return result



def create_text_message(body: str, preview_url: bool = False) -> Dict[str, Any]:
    """Creates a WhatsApp text message structure."""
    return {"type": "text", "text": {"body": body, "preview_url": preview_url}}

def create_image_message(media_id: str, caption: Optional[str] = None) -> Dict[str, Any]:
    """Creates a WhatsApp image message structure."""
    message = {"type": "image", "image": {"id": media_id}}
    if caption:
        message["image"]["caption"] = caption
    return message

def create_document_message(media_id: str, filename: str, caption: Optional[str] = None) -> Dict[str, Any]:
    """Creates a WhatsApp document message structure."""
    message = {"type": "document", "document": {"id": media_id, "filename": filename}}
    if caption:
        message["document"]["caption"] = caption
    return message
