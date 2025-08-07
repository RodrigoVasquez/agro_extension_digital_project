"""
Configuration management for WhatsApp webhook application.
"""

import os
import logging
from typing import Optional, List, Union
from enum import Enum


class AppType(Enum):
    """Application types for webhook handling."""
    AA = "aa"  # Estandar AA
    PP = "pp"  # Estandar PP


class AgentConfig:
    """Configuration for the Agent service."""
    
    def __init__(self):
        self.url: Optional[str] = os.getenv("APP_URL")
        self.timeout: int = int(os.getenv("AGENT_TIMEOUT", "30"))
    
    def validate(self) -> List[str]:
        """Validate agent configuration."""
        missing = []
        if not self.url:
            missing.append("APP_URL")
        return missing


class WhatsAppConfig:
    """Configuration for WhatsApp webhook and API."""
    
    def __init__(self, app_type: AppType):
        self.app_type = app_type
        self._app_suffix = app_type.value.upper()
        
        # WhatsApp API configuration
        self.api_url: Optional[str] = os.getenv(f"ESTANDAR_{self._app_suffix}_FACEBOOK_APP")
        self.token: Optional[str] = self._get_token()
        self.verify_token: Optional[str] = self._get_verify_token()
        
        # App configuration
        self.app_name: Optional[str] = os.getenv(f"ESTANDAR_{self._app_suffix}_APP_NAME")
        self.agent_app_name: str = self._get_agent_app_name()
    
    def _get_token(self) -> Optional[str]:
        """Get WhatsApp token with fallback."""
        specific_token = os.getenv(f"WHATSAPP_TOKEN_{self._app_suffix}")
        return specific_token or os.getenv("WSP_TOKEN")
    
    def _get_verify_token(self) -> Optional[str]:
        """Get verify token with fallback."""
        specific_token = os.getenv(f"VERIFY_TOKEN_{self._app_suffix}")
        return specific_token or os.getenv("VERIFY_TOKEN")
    
    def _get_agent_app_name(self) -> str:
        """Get the mapped application name for the agent service."""
        mapping = {
            "AA": "agent_aa_app",
            "PP": "agent_pp_app"
        }
        return mapping.get(self._app_suffix, self._app_suffix.lower())
    
    def validate(self) -> List[str]:
        """Validate WhatsApp configuration."""
        missing = []
        if not self.app_name:
            missing.append(f"ESTANDAR_{self._app_suffix}_APP_NAME")
        if not self.api_url:
            missing.append(f"ESTANDAR_{self._app_suffix}_FACEBOOK_APP")
        if not self.token:
            missing.append(f"WSP_TOKEN or WHATSAPP_TOKEN_{self._app_suffix}")
        if not self.verify_token:
            missing.append(f"VERIFY_TOKEN or VERIFY_TOKEN_{self._app_suffix}")
        return missing


class AppConfig:
    """Main application configuration."""
    
    def __init__(self):
        self.port: int = int(os.getenv("PORT", "8080"))
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.version: str = "0.2.0"
        
        # Initialize sub-configurations
        self.agent = AgentConfig()
    
    def get_whatsapp_config(self, app_type: Union[AppType, str]) -> WhatsAppConfig:
        """Get WhatsApp configuration for a specific app type."""
        if isinstance(app_type, str):
            app_type = AppType(app_type.lower())
        return WhatsAppConfig(app_type)
    
    @property
    def is_development(self) -> bool:
        """Check if running in a development environment."""
        return self.environment.lower() in ("dev", "development", "local")
    
    def validate(self) -> List[str]:
        """Validate all configurations."""
        missing = []
        missing.extend(self.agent.validate())
        return missing


# Global configuration instance
config = AppConfig()