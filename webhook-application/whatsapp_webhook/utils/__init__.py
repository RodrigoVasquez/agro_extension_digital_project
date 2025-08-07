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
    # Logging
    "get_logger",
    "setup_logging",
    "StructuredLogger",
    "LogContext"
]
