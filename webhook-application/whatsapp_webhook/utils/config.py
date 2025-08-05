"""
Configuration utilities for the WhatsApp webhook application.
"""
import os
from typing import Optional


def get_whatsapp_api_url(app_name: str) -> str:
    """
    Obtiene URL de WhatsApp API según la app.
    
    Args:
        app_name: Nombre de la aplicación (AA, PP, etc.)
        
    Returns:
        str: URL de la API de WhatsApp para la aplicación
    """
    match app_name.upper():
        case "AA":
            return os.getenv("WHATSAPP_API_URL_AA", "")
        case "PP":
            return os.getenv("WHATSAPP_API_URL_PP", "")
        case _:
            return os.getenv("WHATSAPP_API_URL_DEFAULT", "")


def get_whatsapp_token(app_name: str) -> str:
    """
    Obtiene token de WhatsApp según la app.
    
    Args:
        app_name: Nombre de la aplicación (AA, PP, etc.)
        
    Returns:
        str: Token de autenticación de WhatsApp
    """
    match app_name.upper():
        case "AA":
            return os.getenv("WHATSAPP_TOKEN_AA", os.getenv("WSP_TOKEN", ""))
        case "PP":
            return os.getenv("WHATSAPP_TOKEN_PP", os.getenv("WSP_TOKEN", ""))
        case _:
            return os.getenv("WHATSAPP_TOKEN_DEFAULT", os.getenv("WSP_TOKEN", ""))


def get_agent_app_name(app_name: str) -> str:
    """
    Mapea nombres de aplicación de webhook a nombres esperados por el agente.
    
    Args:
        app_name: Nombre de la aplicación del webhook (AA, PP, etc.)
        
    Returns:
        str: Nombre de la aplicación esperado por el agente
    """
    app_name_mapping = {
        "AA": "agent_aa_app",
        "PP": "agent_pp_app"
    }
    
    return app_name_mapping.get(app_name.upper(), app_name.lower())


def get_agent_url() -> str:
    """
    Obtiene la URL del servicio de agente.
    
    Returns:
        str: URL del servicio de agente
    """
    return os.getenv("APP_URL", "")


def get_facebook_app_env_var(app_name: str) -> str:
    """
    Obtiene el nombre de la variable de entorno para la URL de Facebook según la app.
    
    Args:
        app_name: Nombre de la aplicación (AA, PP, etc.)
        
    Returns:
        str: Nombre de la variable de entorno
    """
    match app_name.upper():
        case "AA":
            return "FACEBOOK_APP_AA"
        case "PP":
            return "FACEBOOK_APP_PP"
        case _:
            return "FACEBOOK_APP_DEFAULT"


def get_app_name_env_var(app_name: str) -> str:
    """
    Obtiene el nombre de la variable de entorno para el nombre de la app.
    
    Args:
        app_name: Nombre de la aplicación (AA, PP, etc.)
        
    Returns:
        str: Nombre de la variable de entorno
    """
    match app_name.upper():
        case "AA":
            return "APP_NAME_AA"
        case "PP":
            return "APP_NAME_PP"
        case _:
            return "APP_NAME_DEFAULT"


def validate_environment_config(app_name: str) -> list[str]:
    """
    Valida que las variables de entorno necesarias estén configuradas.
    
    Args:
        app_name: Nombre de la aplicación a validar
        
    Returns:
        list: Lista de variables faltantes (vacía si todo está OK)
    """
    missing_vars = []
    
    # Variables requeridas básicas
    required_vars = [
        "APP_URL",
        get_app_name_env_var(app_name),
        get_facebook_app_env_var(app_name)
    ]
    
    # Verificar token de WhatsApp
    if not get_whatsapp_token(app_name):
        missing_vars.append(f"WSP_TOKEN or WHATSAPP_TOKEN_{app_name.upper()}")
    
    # Verificar otras variables requeridas
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return missing_vars


def get_whatsapp_config(app_name: str) -> dict:
    """
    Obtiene configuración completa de WhatsApp para una app.
    
    Args:
        app_name: Nombre de la aplicación
        
    Returns:
        dict: Configuración con api_url y token
    """
    return {
        "api_url": get_whatsapp_api_url(app_name),
        "token": get_whatsapp_token(app_name)
    }
