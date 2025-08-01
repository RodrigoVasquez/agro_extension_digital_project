"""
Authentication utilities for the WhatsApp webhook application.
"""
from .google_auth import idtoken_from_metadata_server

__all__ = ["idtoken_from_metadata_server"]
