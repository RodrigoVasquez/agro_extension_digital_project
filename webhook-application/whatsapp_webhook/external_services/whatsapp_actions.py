"""
WhatsApp Business API actions for typing indicators and message status.
"""
import httpx
import logging
from typing import Literal, Optional, Dict, Any
from ..utils.logging import get_logger

# Type definitions for WhatsApp actions
WhatsAppAction = Literal["mark_seen", "typing"]

async def send_whatsapp_action(
    to: str,
    action: WhatsAppAction,
    whatsapp_api_url: str,
    token: str
) -> Dict[str, Any]:
    """
    Send a WhatsApp action (typing indicator or mark as read).
    
    Args:
        to: Recipient phone number (with or without +)
        action: Action type ("mark_seen" or "typing")  
        whatsapp_api_url: WhatsApp API endpoint URL
        token: WhatsApp API token
        
    Returns:
        Response from WhatsApp API
        
    Raises:
        httpx.HTTPStatusError: If the request fails
    """
    logger = get_logger("whatsapp_actions")
    
    if not to.startswith("+"):
        to = f"+{to}"
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual", 
        "to": to,
        "action": action
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"Sending WhatsApp action '{action}' to {to}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(whatsapp_api_url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        logger.info(f"WhatsApp action '{action}' sent successfully: {result}")
        return result


async def send_typing_indicator(
    to: str,
    whatsapp_api_url: str,
    token: str
) -> Optional[Dict[str, Any]]:
    """
    Send typing indicator to show the user that a response is being prepared.
    
    Args:
        to: Recipient phone number
        whatsapp_api_url: WhatsApp API endpoint URL  
        token: WhatsApp API token
        
    Returns:
        API response or None if failed
    """
    logger = get_logger("typing_indicator")
    
    try:
        result = await send_whatsapp_action(to, "typing", whatsapp_api_url, token)
        logger.info(f"Typing indicator sent to {to}")
        return result
    except Exception as e:
        logger.error(f"Failed to send typing indicator to {to}: {e}", exc_info=True)
        return None


async def mark_message_as_read(
    to: str,
    whatsapp_api_url: str,
    token: str
) -> Optional[Dict[str, Any]]:
    """
    Mark the conversation as read (blue checkmarks for user).
    
    Args:
        to: Recipient phone number
        whatsapp_api_url: WhatsApp API endpoint URL
        token: WhatsApp API token
        
    Returns:
        API response or None if failed
    """
    logger = get_logger("mark_read")
    
    try:
        result = await send_whatsapp_action(to, "mark_seen", whatsapp_api_url, token) 
        logger.info(f"Message marked as read for {to}")
        return result
    except Exception as e:
        logger.error(f"Failed to mark message as read for {to}: {e}", exc_info=True)
        return None


class TypingContext:
    """
    Context manager for typing indicator that automatically stops typing
    when the context exits or after a timeout.
    """
    
    def __init__(
        self,
        to: str,
        whatsapp_api_url: str,
        token: str,
        auto_mark_read: bool = True
    ):
        self.to = to
        self.whatsapp_api_url = whatsapp_api_url
        self.token = token
        self.auto_mark_read = auto_mark_read
        self.logger = get_logger("typing_context")
    
    async def __aenter__(self):
        """Start typing indicator when entering context."""
        try:
            if self.auto_mark_read:
                await mark_message_as_read(self.to, self.whatsapp_api_url, self.token)
            
            await send_typing_indicator(self.to, self.whatsapp_api_url, self.token)
            self.logger.info(f"Started typing context for {self.to}")
        except Exception as e:
            self.logger.error(f"Failed to start typing context for {self.to}: {e}")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Typing indicator automatically stops when context exits."""
        self.logger.info(f"Ended typing context for {self.to}")
        # Note: Typing indicator stops automatically when a message is sent
        # or after about 15 seconds of inactivity
