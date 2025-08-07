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
        response = await client.post(whatsapp_api_url, json=payload, headers=headers)
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

async def download_whatsapp_media(media_id: str, whatsapp_api_url: str, token: str) -> Optional[bytes]:
    """Downloads media content from WhatsApp using the media ID."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # First, get the media URL
    media_url_endpoint = f"{whatsapp_api_url.replace('/messages', '')}/{media_id}"
    
    logging.info(f"Getting media URL for ID: {media_id}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get media info
            media_response = await client.get(media_url_endpoint, headers=headers)
            media_response.raise_for_status()
            media_info = media_response.json()
            
            if "url" not in media_info:
                logging.error(f"No URL found in media response: {media_info}")
                return None
            
            # Download the actual media content
            media_content_response = await client.get(media_info["url"], headers=headers)
            media_content_response.raise_for_status()
            
            logging.info(f"Media downloaded successfully, size: {len(media_content_response.content)} bytes")
            return media_content_response.content
            
        except Exception as e:
            logging.error(f"Error downloading media {media_id}: {e}", exc_info=True)
            return None
