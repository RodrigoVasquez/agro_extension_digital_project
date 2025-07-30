"""
DEPRECATED: This file is being phased out in favor of the utils/ package.

For backward compatibility, we re-export the main functions.
Please update imports to use the specific modules:

- Auth: whatsapp_webhook.auth.google_auth
- External services: whatsapp_webhook.external_services.agent_client, whatsapp_webhook.external_services.whatsapp_client  
- Utils: whatsapp_webhook.utils.helpers, whatsapp_webhook.utils.config, whatsapp_webhook.utils.logging
"""
import warnings

# Re-export auth functions for backward compatibility
from .auth.google_auth import idtoken_from_metadata_server, get_id_token

# Re-export helper functions
from .utils.helpers import (
    generate_session_id,
    sanitize_user_id,
    validate_phone_number,
    normalize_phone_number
)

# Re-export config functions  
from .utils.config import (
    get_whatsapp_api_url,
    get_whatsapp_token,
    get_agent_url
)

# Re-export logging functions
from .utils.logging import get_logger, setup_logging

# Issue deprecation warning
warnings.warn(
    "whatsapp_webhook.utils is deprecated. Use specific modules: "
    "whatsapp_webhook.auth, whatsapp_webhook.external_services, whatsapp_webhook.utils",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    # Auth (deprecated - use whatsapp_webhook.auth.google_auth)
    "idtoken_from_metadata_server",
    "get_id_token",
    # Helpers (deprecated - use whatsapp_webhook.utils.helpers)
    "generate_session_id",
    "sanitize_user_id", 
    "validate_phone_number",
    "normalize_phone_number",
    # Config (deprecated - use whatsapp_webhook.utils.config)
    "get_whatsapp_api_url",
    "get_whatsapp_token",
    "get_agent_url",
    # Logging (deprecated - use whatsapp_webhook.utils.logging)
    "get_logger",
    "setup_logging"
]