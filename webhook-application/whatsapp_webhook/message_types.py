"""
Message type definitions and enums for WhatsApp webhook processing.
"""
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class MessageType(Enum):
    """Supported WhatsApp message types."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACTS = "contacts"
    INTERACTIVE = "interactive"
    REACTION = "reaction"
    TEMPLATE = "template"
    UNSUPPORTED = "unsupported"


@dataclass
class MessageData:
    """Structured representation of a WhatsApp message."""
    message_id: str
    user_wa_id: str
    message_type: MessageType
    timestamp: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    # Type-specific data
    text_content: Optional[str] = None
    media_id: Optional[str] = None
    media_caption: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None
    contact_data: Optional[Dict[str, Any]] = None
    interactive_data: Optional[Dict[str, Any]] = None
    reaction_data: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingContext:
    """Context data needed for message processing."""
    app_name: str
    whatsapp_api_url: str
    wsp_token: str
    user_wa_id: str
    session_id: str


class MessageError(Exception):
    """Base exception for message processing errors."""
    pass


class UnsupportedMessageTypeError(MessageError):
    """Raised when encountering an unsupported message type."""
    pass


class MessageParsingError(MessageError):
    """Raised when message parsing fails."""
    pass


class MessageProcessingError(MessageError):
    """Raised when message processing fails."""
    pass
