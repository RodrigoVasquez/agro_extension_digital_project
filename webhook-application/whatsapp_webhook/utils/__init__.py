"""
General utilities for the WhatsApp webhook application.
"""
from .helpers import (
    generate_session_id, 
    sanitize_user_id, 
    validate_phone_number,
    normalize_phone_number,
    create_message_hash,
    truncate_text,
    extract_media_type,
    is_supported_image_type,
    is_supported_document_type
)
from .config import (
    get_whatsapp_api_url, 
    get_whatsapp_token, 
    get_agent_url,
    validate_environment_config
)
from .logging import (
    get_logger, 
    setup_logging, 
    StructuredLogger, 
    LogContext
)

__all__ = [
    # Helpers
    "generate_session_id",
    "sanitize_user_id", 
    "validate_phone_number",
    "normalize_phone_number",
    "create_message_hash",
    "truncate_text",
    "extract_media_type",
    "is_supported_image_type",
    "is_supported_document_type",
    # Config
    "get_whatsapp_api_url",
    "get_whatsapp_token",
    "get_agent_url",
    "validate_environment_config",
    # Logging
    "get_logger",
    "setup_logging",
    "StructuredLogger",
    "LogContext"
]
