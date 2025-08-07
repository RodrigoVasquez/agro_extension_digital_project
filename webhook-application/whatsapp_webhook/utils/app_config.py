"""
Configuration management for WhatsApp webhook application.
"""

import os
import logging
from typing import Optional, List, Union, Dict
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
        
        # Available agent applications
        self.available_agents = {
            "agent_aa_app": "agent_aa_app",
            "agent_pp_app": "agent_pp_app"
        }
        
        # Agent paths for sessions (these need the full path)
        self.agent_session_paths = {
            "agent_aa_app": "/apps/agent_aa_app",
            "agent_pp_app": "/apps/agent_pp_app"
        }
    
    def get_run_url(self) -> Optional[str]:
        """Get the run endpoint URL."""
        if not self.url:
            return None
        return f"{self.url}/run"
    
    def get_agent_session_url(self, agent_name: str, user_id: str, session_id: str) -> Optional[str]:
        """Get the complete session URL for a specific agent."""
        if not self.url:
            return None
        
        agent_path = self.agent_session_paths.get(agent_name)
        if not agent_path:
            return None
            
        return f"{self.url}{agent_path}/users/{user_id}/sessions/{session_id}"
    
    def validate(self) -> List[str]:
        """Validate agent configuration."""
        missing = []
        if not self.url:
            missing.append("APP_URL")
        return missing


class WhatsAppConfig:
    """Configuration for WhatsApp webhook and API."""
    
    def __init__(self, app_type: AppType, agent_config: AgentConfig):
        self.app_type = app_type
        self._app_suffix = app_type.value.upper()
        self._agent_config = agent_config
        
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
    
    def get_agent_run_url(self) -> Optional[str]:
        """Get the run endpoint URL."""
        return self._agent_config.get_run_url()
    
    def get_agent_session_url(self, user_id: str, session_id: str, agent_name: Optional[str] = None) -> Optional[str]:
        """Get the complete agent session endpoint URL."""
        target_agent = agent_name or self.agent_app_name
        return self._agent_config.get_agent_session_url(target_agent, user_id, session_id)
    
    def get_available_agents(self) -> Dict[str, str]:
        """Get all available agents."""
        return self._agent_config.available_agents
    
    def can_route_to_agent(self, agent_name: str) -> bool:
        """Check if this config can route to a specific agent."""
        return agent_name in self._agent_config.available_agents
    
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
        return WhatsAppConfig(app_type, self.agent)
    
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