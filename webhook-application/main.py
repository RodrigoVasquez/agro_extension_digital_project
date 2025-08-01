"""
WhatsApp Webhook Service - Main application entry point.

This module provides a clean, modular entry point for the WhatsApp webhook service
using FastAPI with proper separation of concerns and configuration management.
"""

import uvicorn
from whatsapp_webhook.app import create_app
from whatsapp_webhook.utils.app_config import config
from whatsapp_webhook.utils.logging import get_logger

# Create application instance
app = create_app()

# Get logger for main module
logger = get_logger("main")


if __name__ == "__main__":
    logger.info(
        f"Starting WhatsApp Webhook Service",
        extra={
            "host": config.host,
            "port": config.port,
            "environment": config.environment,
            "log_level": config.log_level
        }
    )
    
    uvicorn.run(
        app, 
        host=config.host, 
        port=config.port,
        access_log=config.is_development,
        reload=config.is_development
    )