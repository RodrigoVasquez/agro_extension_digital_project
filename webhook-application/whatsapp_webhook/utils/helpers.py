"""
Helper utilities for the WhatsApp webhook application.
"""
import re
import uuid
import hashlib
from typing import Optional
from datetime import datetime


def generate_session_id(user_wa_id: str) -> str:
    """
    Genera un session ID único basado en el user_wa_id.
    
    Args:
        user_wa_id: ID de WhatsApp del usuario
        
    Returns:
        str: Session ID único
    """
    # Por ahora usar el mismo user_wa_id como session_id
    # En el futuro podríamos generar algo más sofisticado
    return user_wa_id


def sanitize_user_id(user_id: str) -> str:
    """
    Sanitiza el user ID para logging seguro (enmascara parcialmente).
    
    Args:
        user_id: ID del usuario original
        
    Returns:
        str: ID sanitizado para logging
    """
    if len(user_id) <= 4:
        return "****"
    
    return user_id[:2] + "*" * (len(user_id) - 4) + user_id[-2:]


def validate_phone_number(phone: str) -> bool:
    """
    Valida formato básico de número de teléfono.
    
    Args:
        phone: Número de teléfono a validar
        
    Returns:
        bool: True si el formato es válido
    """
    # Remover espacios y caracteres especiales
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # Verificar formato básico (al menos 7 dígitos, opcionalmente con +)
    pattern = r'^\+?[1-9]\d{6,14}$'
    return bool(re.match(pattern, clean_phone))


def normalize_phone_number(phone: str) -> str:
    """
    Normaliza un número de teléfono al formato internacional.
    
    Args:
        phone: Número de teléfono a normalizar
        
    Returns:
        str: Número normalizado con + al inicio
    """
    # Remover espacios y caracteres especiales excepto +
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # Agregar + si no lo tiene
    if not clean_phone.startswith('+'):
        clean_phone = f'+{clean_phone}'
    
    return clean_phone


def create_message_hash(content: str, user_id: str) -> str:
    """
    Crea un hash único para un mensaje (útil para deduplicación).
    
    Args:
        content: Contenido del mensaje
        user_id: ID del usuario
        
    Returns:
        str: Hash MD5 del mensaje
    """
    message_string = f"{user_id}:{content}:{datetime.utcnow().date()}"
    return hashlib.md5(message_string.encode()).hexdigest()


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Trunca texto para logging o display.
    
    Args:
        text: Texto original
        max_length: Longitud máxima permitida
        
    Returns:
        str: Texto truncado con "..." si es necesario
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def extract_media_type(mime_type: str) -> str:
    """
    Extrae el tipo de media del MIME type.
    
    Args:
        mime_type: MIME type completo (e.g., "image/jpeg")
        
    Returns:
        str: Tipo de media (e.g., "image")
    """
    return mime_type.split('/')[0] if '/' in mime_type else mime_type


def is_supported_image_type(mime_type: str) -> bool:
    """
    Verifica si el tipo de imagen es soportado por WhatsApp.
    
    Args:
        mime_type: MIME type de la imagen
        
    Returns:
        bool: True si es soportado
    """
    supported_types = {
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/webp'
    }
    return mime_type.lower() in supported_types


def is_supported_document_type(mime_type: str) -> bool:
    """
    Verifica si el tipo de documento es soportado por WhatsApp.
    
    Args:
        mime_type: MIME type del documento
        
    Returns:
        bool: True si es soportado
    """
    supported_types = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        'text/csv'
    }
    return mime_type.lower() in supported_types
