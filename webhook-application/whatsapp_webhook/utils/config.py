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
    import logging
    
    app_upper = app_name.upper()
    
    # URLs base para cada aplicación (extraídas de FACEBOOK_APP env vars)
    app_urls = {
        "AA": "https://graph.facebook.com/v22.0/692894087240362",
        "PP": "https://graph.facebook.com/v22.0/619189944620159"
    }
    
    # Intentar obtener la URL específica desde variables de entorno primero
    if app_upper == "AA":
        url = os.getenv("WHATSAPP_API_URL_AA")
        env_var = "WHATSAPP_API_URL_AA"
        default_url = app_urls["AA"]
    elif app_upper == "PP":
        url = os.getenv("WHATSAPP_API_URL_PP")
        env_var = "WHATSAPP_API_URL_PP"
        default_url = app_urls["PP"]
    else:
        url = os.getenv("WHATSAPP_API_URL_DEFAULT")
        env_var = "WHATSAPP_API_URL_DEFAULT"
        default_url = None
    
    # Si no encuentra la específica, intentar variables generales
    if not url:
        url = os.getenv("WHATSAPP_API_URL")
        if not url and default_url:
            # Usar URL por defecto basada en FACEBOOK_APP
            url = default_url
            logging.info(f"Usando URL por defecto para app {app_name}: {url}")
        elif url:
            logging.info(f"Usando WHATSAPP_API_URL genérica para app {app_name}: {url}")
        else:
            logging.error(f"No se encontró configuración de URL para app {app_name}. Variables intentadas: {env_var}, WHATSAPP_API_URL")
            return ""
    else:
        logging.debug(f"URL de WhatsApp para app {app_name}: {url}")
    
    return url


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
    import logging
    
    api_url = get_whatsapp_api_url(app_name)
    token = get_whatsapp_token(app_name)
    
    config = {
        "api_url": api_url,
        "token": token
    }
    
    # Log de configuración para diagnóstico
    logging.info(f"Configuración WhatsApp para app {app_name}: api_url='{api_url}', token={'***' if token else 'VACIO'}")
    
    if not api_url:
        logging.error(f"⚠️  CONFIGURACIÓN INCOMPLETA: api_url está vacío para app {app_name}")
    if not token:
        logging.error(f"⚠️  CONFIGURACIÓN INCOMPLETA: token está vacío para app {app_name}")
    
    return config
