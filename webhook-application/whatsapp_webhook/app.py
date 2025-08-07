"""
FastAPI application factory and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tomllib

from .api.webhooks import router as webhook_router
from .utils.logging import configure_app_logging
from .utils.app_config import config
from .models.api_models import HealthCheckResponse


def get_version() -> str:
    """Get version from pyproject.toml."""
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
            return data["project"]["version"]
    except Exception:
        return "unknown"


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    # Configure logging first
    app_logger = configure_app_logging()
    
    # Get version from pyproject.toml
    version = get_version()
    
    # Create FastAPI app with metadata
    app = FastAPI(
        title="WhatsApp Webhook Service",
        description="Modular WhatsApp webhook processor for handling various message types and integrating with AI agent services",
        version=version,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
            version=version,
            environment="production"
        )
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return JSONResponse(
            content={
                "service": "WhatsApp Webhook Service",
                "version": version,
                "status": "running",
                "environment": "production"
            }
        )
    
    app_logger.info(f"FastAPI application created successfully", extra={
        "version": version,
        "environment": "production"
    })
    
    return app
