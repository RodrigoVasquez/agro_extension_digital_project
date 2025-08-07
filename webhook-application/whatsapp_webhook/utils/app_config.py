"""
Configuration management for WhatsApp webhook application.
"""

import os
import logging
from typing import Optional, List
from enum import Enum


class AppType(Enum):
    """Application types for webhook handling."""
    AA = "aa"  # Estandar AA
    PP = "pp"  # Estandar PP


class WebhookConfig:
    """Configuration for a specific webhook type (AA or PP)."""
    
    def __init__(self, app_type: AppType, global_config: 'AppConfig'):
        self.app_type = app_type
        self._app_suffix = app_type.value.upper()
        self._global_config = global_config

    @property
    def app_name(self) -> Optional[str]:
        """Get the application name from environment variables."""
        return os.getenv(f"ESTANDAR_{self._app_suffix}_APP_NAME")

    @property
    def verify_token(self) -> Optional[str]:
        """Get verification token, falling back to a global token."""
        specific_token = os.getenv(f"VERIFY_TOKEN_{self._app_suffix}")
        return specific_token or self._global_config.wsp_verify_token

    @property
    def whatsapp_api_url(self) -> Optional[str]:
        """Get the WhatsApp API base URL."""
        return os.getenv(f"ESTANDAR_{self._app_suffix}_FACEBOOK_APP")

    @property
    def whatsapp_token(self) -> Optional[str]:
        """Get the WhatsApp API token, falling back to a global token."""
        specific_token = os.getenv(f"WHATSAPP_TOKEN_{self._app_suffix}")
        return specific_token or self._global_config.wsp_token

    @property
    def agent_app_name(self) -> str:
        """Get the mapped application name for the agent service."""
        mapping = {
            "AA": "agent_aa_app",
            "PP": "agent_pp_app"
        }
        return mapping.get(self._app_suffix, self._app_suffix.lower())

    def get_full_config(self) -> dict:
        """Return a dictionary with the full WhatsApp configuration for this app type."""
        config_dict = {
            "api_url": self.whatsapp_api_url,
            "token": self.whatsapp_token,
            "app_name": self.app_name,
            "agent_app_name": self.agent_app_name
        }
        if not config_dict["api_url"] or not config_dict["token"]:
            logging.warning(f"Incomplete configuration for app {self.app_type.value}")
        return config_dict

    def validate(self) -> List[str]:
        """Validate required environment variables for this app type."""
        missing = []
        if not self.app_name:
            missing.append(f"ESTANDAR_{self._app_suffix}_APP_NAME")
        if not self.whatsapp_api_url:
            missing.append(f"ESTANDAR_{self._app_suffix}_FACEBOOK_APP")
        if not self.whatsapp_token:
            missing.append(f"WSP_TOKEN or WHATSAPP_TOKEN_{self._app_suffix}")
        return missing


class AppConfig:
    """Main application configuration, loaded from environment variables."""
    
    def __init__(self):
        self.port: int = int(os.getenv("PORT", "8080"))
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.version: str = "0.2.0"  # Version updated

        # Global service URLs and tokens
        self.agent_url: Optional[str] = os.getenv("APP_URL")
        self.wsp_token: Optional[str] = os.getenv("WSP_TOKEN")
        self.wsp_verify_token: Optional[str] = os.getenv("VERIFY_TOKEN")

    def get_webhook_config(self, app_type: AppType) -> WebhookConfig:
        """Get webhook configuration for a specific app type."""
        return WebhookConfig(app_type, self)

    @property
    def is_development(self) -> bool:
        """Check if running in a development environment."""
        return self.environment.lower() in ("dev", "development", "local")

    def validate_global(self) -> List[str]:
        """Validate core application environment variables."""
        missing = []
        if not self.agent_url:
            missing.append("APP_URL")
        return missing


# Create a single, global instance of the configuration
config = AppConfig()