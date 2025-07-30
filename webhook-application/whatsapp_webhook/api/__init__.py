"""
API module for WhatsApp webhook application.
"""

from .webhooks import router as webhook_router

__all__ = ["webhook_router"]
