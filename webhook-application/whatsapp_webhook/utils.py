"""
DEPRECATED: This file is being phased out in favor of the new modular structure.

Please update imports to use the specific modules:
- Auth: whatsapp_webhook.auth.google_auth
- External services: whatsapp_webhook.external_services
- Utils: whatsapp_webhook.utils.app_config, whatsapp_webhook.utils.helpers, whatsapp_webhook.utils.logging
"""
import warnings

# Re-export for backward compatibility
from .auth.google_auth import idtoken_from_metadata_server, get_id_token
from .helpers import (
    generate_session_id,
    sanitize_user_id,
    validate_phone_number,
    normalize_phone_number
)
from .logging import get_logger, setup_logging

warnings.warn(
    "whatsapp_webhook.utils is deprecated. Use specific modules in the utils package.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "idtoken_from_metadata_server",
    "get_id_token",
    "generate_session_id",
    "sanitize_user_id", 
    "validate_phone_number",
    "normalize_phone_number",
    "get_logger",
    "setup_logging"
]