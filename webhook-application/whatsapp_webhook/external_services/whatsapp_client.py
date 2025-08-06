"""
WhatsApp API client utilities for sending messages and downloading media.
"""
import httpx
import logging
from typing import Any, Dict, Optional


async def send_whatsapp_message(
    to: str,
    message: Dict[str, Any],
    whatsapp_api_url: str,
    token: str
) -> Dict[str, Any]:
    """
    Envía mensaje a WhatsApp API - función simple y clara.
    
    Args:
        to: Número de teléfono del destinatario
        message: Contenido del mensaje estructurado
        whatsapp_api_url: URL base de la API de WhatsApp
        token: Token de autenticación
        
    Returns:
        dict: Respuesta de la API de WhatsApp
        
    Raises:
        httpx.HTTPError: Si la comunicación con WhatsApp falla
    """
    # Asegurarse de que el número tenga formato correcto
    if not to.startswith("+"):
        to = f"+{to}"
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        **message
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    logging.info(f"Sending WhatsApp message to {to}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{whatsapp_api_url}/messages",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        
        result = response.json()
        logging.info(f"WhatsApp message sent successfully: {result}")
        return result


async def download_whatsapp_media(
    media_id: str,
    whatsapp_api_url: str,
    token: str
) -> bytes:
    """
    Descarga media de WhatsApp - función directa.
    
    Args:
        media_id: ID del archivo multimedia en WhatsApp
        whatsapp_api_url: URL base de la API de WhatsApp
        token: Token de autenticación
        
    Returns:
        bytes: Contenido del archivo multimedia
        
    Raises:
        httpx.HTTPError: Si la descarga falla
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    logging.info(f"Downloading WhatsApp media: {media_id}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Primero obtener la URL de descarga
        media_response = await client.get(
            f"{whatsapp_api_url}/{media_id}",
            headers=headers
        )
        media_response.raise_for_status()
        
        media_info = media_response.json()
        download_url = media_info.get("url")
        
        if not download_url:
            raise ValueError(f"No download URL found for media {media_id}")
        
        # Descargar el archivo
        file_response = await client.get(download_url, headers=headers)
        file_response.raise_for_status()
        
        logging.info(f"Media downloaded successfully: {len(file_response.content)} bytes")
        return file_response.content


def create_text_message(body: str, preview_url: bool = False) -> Dict[str, Any]:
    """
    Crea un mensaje de texto para WhatsApp.
    
    Args:
        body: Contenido del mensaje
        preview_url: Si mostrar preview de URLs
        
    Returns:
        dict: Estructura del mensaje de texto
    """
    return {
        "type": "text",
        "text": {
            "body": body,
            "preview_url": preview_url
        }
    }


def create_image_message(media_id: str, caption: Optional[str] = None) -> Dict[str, Any]:
    """
    Crea un mensaje de imagen para WhatsApp.
    
    Args:
        media_id: ID de la imagen en WhatsApp
        caption: Texto opcional que acompaña la imagen
        
    Returns:
        dict: Estructura del mensaje de imagen
    """
    message = {
        "type": "image",
        "image": {
            "id": media_id
        }
    }
    
    if caption:
        message["image"]["caption"] = caption
        
    return message


def create_document_message(media_id: str, filename: str, caption: Optional[str] = None) -> Dict[str, Any]:
    """
    Crea un mensaje de documento para WhatsApp.
    
    Args:
        media_id: ID del documento en WhatsApp
        filename: Nombre del archivo
        caption: Texto opcional que acompaña el documento
        
    Returns:
        dict: Estructura del mensaje de documento
    """
    message = {
        "type": "document",
        "document": {
            "id": media_id,
            "filename": filename
        }
    }
    
    if caption:
        message["document"]["caption"] = caption
        
    return message


async def download_media(media_id: str, whatsapp_api_url: str, token: str) -> Optional[bytes]:
    """Descarga media de WhatsApp."""
    try:
        # Validar que whatsapp_api_url tenga el formato correcto
        if not whatsapp_api_url:
            logging.error(f"whatsapp_api_url está vacío para media_id: {media_id}")
            return None
            
        if not whatsapp_api_url.startswith(("http://", "https://")):
            logging.error(f"whatsapp_api_url no tiene protocolo válido: '{whatsapp_api_url}' para media_id: {media_id}")
            return None
        
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            # Obtener URL del media
            media_info_url = f"{whatsapp_api_url}/{media_id}"
            logging.info(f"Obteniendo información de media desde: {media_info_url}")
            logging.debug(f"whatsapp_api_url original: '{whatsapp_api_url}'")
            
            resp = await client.get(media_info_url, headers=headers)
            resp.raise_for_status()
            file_url = resp.json().get("url")
            
            if file_url:
                logging.info(f"Descargando archivo de audio desde URL: {file_url}")
                # Descargar contenido
                content_resp = await client.get(file_url, headers=headers)
                content_resp.raise_for_status()
                
                content_size = len(content_resp.content)
                logging.info(f"Audio descargado exitosamente: {content_size} bytes desde {file_url}")
                return content_resp.content
            else:
                logging.warning(f"No se encontró URL de descarga para media_id: {media_id}")
                return None
    except Exception as e:
        logging.error(f"Error descargando media {media_id} con URL '{whatsapp_api_url}': {e}")
    return None
