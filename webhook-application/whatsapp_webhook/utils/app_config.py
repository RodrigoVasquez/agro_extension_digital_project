"""
Simplified and centralized configuration management for the WhatsApp webhook application.
"""

import os
from pydantic import BaseModel, Field
from typing import Optional

class AppSpecificConfig(BaseModel):
    """Configuration specific to an application like AA or PP."""
    facebook_app_url: Optional[str]
    app_name: Optional[str]
    verify_token: Optional[str]
    wsp_token: Optional[str]

class AppConfig(BaseModel):
    """Main application configuration, loaded directly from environment variables."""
    agent_url: Optional[str] = Field(alias="APP_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # App-specific nested configurations
    aa: AppSpecificConfig
    pp: AppSpecificConfig

    class Config:
        allow_population_by_field_name = True

def load_config_from_env() -> AppConfig:
    """Loads the application configuration from environment variables."""
    return AppConfig(
        agent_url=os.getenv("APP_URL"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        aa=AppSpecificConfig(
            facebook_app_url=os.getenv("ESTANDAR_AA_FACEBOOK_APP"),
            app_name=os.getenv("ESTANDAR_AA_APP_NAME"),
            verify_token=os.getenv("VERIFY_TOKEN"),
            wsp_token=os.getenv("WSP_TOKEN"),
        ),
        pp=AppSpecificConfig(
            facebook_app_url=os.getenv("ESTANDAR_PP_FACEBOOK_APP"),
            app_name=os.getenv("ESTANDAR_PP_APP_NAME"),
            verify_token=os.getenv("VERIFY_TOKEN"),
            wsp_token=os.getenv("WSP_TOKEN"),
        ),
    )

# Singleton instance to be used across the application
config = load_config_from_env()
