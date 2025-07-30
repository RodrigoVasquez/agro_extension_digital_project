"""
WhatsApp Webhook Application

A modular WhatsApp webhook processor for handling various message types
and integrating with AI agent services.

Modular Structure:
- auth: Authentication utilities (Google Cloud)
- external_services: Client modules for external APIs (Agent, WhatsApp)
- utils: General utilities (helpers, config, logging)
- message_types: Data structures and enums
- sessions: Session management
- messages: Message processing (legacy, being refactored)

Usage:
    # Authentication
    from whatsapp_webhook.auth.google_auth import idtoken_from_metadata_server
    
    # External services
    from whatsapp_webhook.external_services import send_to_agent, send_whatsapp_message
    
    # Utilities
    from whatsapp_webhook.utils.logging import get_logger
    from whatsapp_webhook.utils.config import get_whatsapp_api_url
    from whatsapp_webhook.utils.helpers import validate_phone_number
    
    # Message types
    from whatsapp_webhook.message_types import MessageType, MessageData
"""

__version__ = "2.0.0"
__author__ = "WhatsApp Webhook Team"

# Export commonly used classes and enums
from .message_types import MessageType, MessageData, ProcessingContext
from .message_types import MessageError, UnsupportedMessageTypeError, MessageParsingError, MessageProcessingError

__all__ = [
    # Version info
    "__version__",
    "__author__",
    # Core types
    "MessageType",
    "MessageData", 
    "ProcessingContext",
    # Exceptions
    "MessageError",
    "UnsupportedMessageTypeError",
    "MessageParsingError", 
    "MessageProcessingError"
]
