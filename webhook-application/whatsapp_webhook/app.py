"""
FastAPI application factory and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from .api.webhooks import router as webhook_router
from .utils.logging import configure_app_logging
from .utils.app_config import config
from .models.api_models import HealthCheckResponse


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    # Configure logging first
    app_logger = configure_app_logging()
    
    # Create FastAPI app with metadata
    app = FastAPI(
        title="WhatsApp Webhook Service",
        description="Modular WhatsApp webhook processor for handling various message types and integrating with AI agent services",
        version=config.version,
        docs_url="/docs" if config.is_development else None,
        redoc_url="/redoc" if config.is_development else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if config.is_development else [],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(webhook_router)
    
    # Add health check endpoint
    @app.get("/health", response_model=HealthCheckResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthCheckResponse(
            status="healthy",
            version=config.version,
            environment=config.environment
        )
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return JSONResponse(
            content={
                "service": "WhatsApp Webhook Service",
                "version": config.version,
                "status": "running",
                "environment": config.environment
            }
        )
    
    app_logger.info(f"FastAPI application created successfully", extra={
        "version": config.version,
        "environment": config.environment,
        "docs_enabled": config.is_development
    })
    
    return app
