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
    
    # Intentar obtener la URL específica desde variables de entorno
    if app_upper == "AA":
        url = os.getenv("ESTANDAR_AA_FACEBOOK_APP")
        env_var = "ESTANDAR_AA_FACEBOOK_APP"
    elif app_upper == "PP":
        url = os.getenv("ESTANDAR_PP_FACEBOOK_APP")
        env_var = "ESTANDAR_PP_FACEBOOK_APP"
    else:
        # Intentar variables de entorno alternativas para otros casos
        url = os.getenv("WHATSAPP_API_URL_DEFAULT") or os.getenv("WHATSAPP_API_URL")
        env_var = "WHATSAPP_API_URL_DEFAULT or WHATSAPP_API_URL"

    if not url:
        logging.error(f"No se encontró configuración de URL para app {app_name}. Variable de entorno {env_var} no está configurada.")
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
            return "ESTANDAR_AA_FACEBOOK_APP"
        case "PP":
            return "ESTANDAR_PP_FACEBOOK_APP"
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
            return "ESTANDAR_AA_APP_NAME"
        case "PP":
            return "ESTANDAR_PP_APP_NAME"
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
