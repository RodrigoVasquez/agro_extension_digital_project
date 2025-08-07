"""
Simplified and centralized configuration management for the WhatsApp webhook application.
"""

import os
from pydantic import BaseModel

class AppConfig(BaseModel):
    """Main application configuration, loaded directly from environment variables."""
    agent_url: str
    log_level: str
    verify_token: str
    wsp_token: str
    
    # App-specific nested configurations
    aa_facebook_app_url: str
    aa_app_name: str
    
    pp_facebook_app_url: str
    pp_app_name: str

def load_config_from_env() -> AppConfig:
    """Loads the application configuration from environment variables."""
    return AppConfig(
        agent_url=os.getenv("APP_URL"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        verify_token=os.getenv("VERIFY_TOKEN"),
        wsp_token=os.getenv("WSP_TOKEN"),
        aa_facebook_app_url=os.getenv("ESTANDAR_AA_FACEBOOK_APP"),
        aa_app_name=os.getenv("ESTANDAR_AA_APP_NAME"),
        pp_facebook_app_url=os.getenv("ESTANDAR_PP_FACEBOOK_APP"),
        pp_app_name=os.getenv("ESTANDAR_PP_APP_NAME"),
    )

# Singleton instance to be used across the application
config = load_config_from_env()
