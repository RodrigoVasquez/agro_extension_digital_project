"""
Utilities for working with Pydantic message models.
"""

from pydantic import ValidationError
from typing import Optional, Dict, Any
import logging

from ..models.messages import (
    WhatsAppWebhookPayload,
    AgentResponse,
    WhatsAppOutgoingMessage,
    WhatsAppOutgoingTextBody,
    MessageProcessingContext,
    AgentRequestPayload
)


def parse_webhook_payload(data: Dict[str, Any]) -> Optional[WhatsAppWebhookPayload]:
    """
    Safely parse webhook payload data into a Pydantic model.
    
    Args:
        data: Raw webhook payload data
        
    Returns:
        Parsed WhatsAppWebhookPayload or None if parsing fails
    """
    try:
        return WhatsAppWebhookPayload.model_validate(data)
    except ValidationError as e:
        logging.error(f"Failed to parse webhook payload: {e}")
        logging.debug(f"Invalid payload data: {data}")
        return None


def parse_agent_response(response_data: list) -> Optional[str]:
    """
    Parse agent response and extract text content.
    
    Args:
        response_data: Raw response list from agent service
        
    Returns:
        Extracted text or None if parsing fails
    """
    if not isinstance(response_data, list) or not response_data:
        logging.warning("Agent response is not a list or is empty")
        return None
        
    try:
        last_event = response_data[-1]
        agent_response = AgentResponse.model_validate(last_event)
        return agent_response.extract_text_response()
    except ValidationError as e:
        logging.error(f"Failed to parse agent response: {e}")
        logging.debug(f"Invalid response data: {last_event}")
        return None


def create_outgoing_text_message(to: str, text: str) -> WhatsAppOutgoingMessage:
    """
    Create a validated outgoing text message.
    
    Args:
        to: Recipient phone number
        text: Message text
        
    Returns:
        Validated WhatsAppOutgoingMessage
        
    Raises:
        ValidationError: If validation fails
    """
    return WhatsAppOutgoingMessage(
        to=to,
        text=WhatsAppOutgoingTextBody(body=text)
    )


def create_processing_context(
    app_name: str,
    user_wa_id: str,
    whatsapp_api_url: str,
    wsp_token: str,
    session_id: Optional[str] = None
) -> MessageProcessingContext:
    """
    Create a validated message processing context.
    
    Args:
        app_name: Application name
        user_wa_id: User WhatsApp ID
        whatsapp_api_url: WhatsApp API URL
        wsp_token: WhatsApp token
        session_id: Session ID (defaults to user_wa_id)
        
    Returns:
        Validated MessageProcessingContext
        
    Raises:
        ValidationError: If validation fails
    """
    return MessageProcessingContext(
        app_name=app_name,
        user_wa_id=user_wa_id,
        session_id=session_id or user_wa_id,
        whatsapp_api_url=whatsapp_api_url,
        wsp_token=wsp_token
    )


def create_agent_request(
    app_name: str,
    user_id: str,
    session_id: str,
    message_text: str,
    streaming: bool = False
) -> AgentRequestPayload:
    """
    Create a validated agent request payload.
    
    Args:
        app_name: Application name
        user_id: User ID
        session_id: Session ID
        message_text: Message text
        streaming: Whether to use streaming
        
    Returns:
        Validated AgentRequestPayload
        
    Raises:
        ValidationError: If validation fails
    """
    return AgentRequestPayload.create_text_request(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        message_text=message_text,
        streaming=streaming
    )
