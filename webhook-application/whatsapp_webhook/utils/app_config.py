"""
Configuration management for WhatsApp webhook application.
"""

import os
from typing import Optional
from enum import Enum


class AppType(Enum):
    """Application types for webhook handling."""
    AA = "aa"  # Estandar AA
    PP = "pp"  # Estandar PP


class WebhookConfig:
    """Configuration for webhook operations."""
    
    def __init__(self, app_type: AppType):
        self.app_type = app_type
        self._app_suffix = app_type.value.upper()
    
    @property
    def verify_token(self) -> Optional[str]:
        """Get verification token for this app type."""
        specific_token = os.getenv(f"VERIFY_TOKEN_{self._app_suffix}")
        fallback_token = os.getenv("VERIFY_TOKEN")
        return specific_token or fallback_token
    
    @property
    def app_name_env_var(self) -> str:
        """Get environment variable name for app name."""
        return f"ESTANDAR_{self._app_suffix}_APP_NAME"
    
    @property
    def facebook_app_env_var(self) -> str:
        """Get environment variable name for Facebook app URL."""
        return f"ESTANDAR_{self._app_suffix}_FACEBOOK_APP"


class AppConfig:
    """Main application configuration."""
    
    def __init__(self):
        self.port = int(os.getenv("PORT", "8080"))
        self.host = os.getenv("HOST", "0.0.0.0")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.app_url = os.getenv("APP_URL")
        self.wsp_token = os.getenv("WSP_TOKEN")
        self.version = "0.1.0"
        self.environment = os.getenv("ENVIRONMENT", "development")
    
    def get_webhook_config(self, app_type: AppType) -> WebhookConfig:
        """Get webhook configuration for specific app type."""
        return WebhookConfig(app_type)
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("dev", "development", "local")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ("prd", "production", "prod")


# Global configuration instance
config = AppConfig()
