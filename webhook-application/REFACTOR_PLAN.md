# 🔄 Plan de Refactor: Manejo de Mensajes WhatsApp

## 📋 Resumen Ejecutivo

Este documento describe el plan de refactor para mejorar el manejo de mensajes de WhatsApp en el sistema webhook, implementando una arquitectura modular y extensible que soporte múltiples tipos de mensajes de manera eficiente.

## 🎯 Objetivos

- **Extensibilidad**: Facilitar la adición de nuevos tipos de mensajes
- **Mantenibilidad**: Código más limpio y fácil de mantener
- **Robustez**: Mejor manejo de errores y casos edge
- **Testabilidad**: Arquitectura que permita testing unitario efectivo
- **Performance**: Procesamiento eficiente de mensajes

## 📊 Análisis del Estado Actual

### ✅ Fortalezas Actuales
- Manejo básico de mensajes de texto funcional
- Sistema de autenticación con tokens ID implementado
- Logging detallado para debugging
- Separación entre apps (AA y PP)

### ❌ Problemas Identificados

1. **Limitación de Tipos de Mensaje**
   - Solo soporta mensajes de texto
   - No hay estructura para manejar multimedia, ubicaciones, contactos, etc.

2. **Código Monolítico**
   - `process_incoming_webhook_payload()` es muy larga (+80 líneas)
   - Mezcla parsing, validación y procesamiento
   - Difícil de testear y mantener

3. **Falta de Abstracción**
   - No hay interfaces claras para diferentes tipos de mensajes
   - Lógica específica mezclada con lógica general

4. **Manejo de Errores Inconsistente**
   - Diferentes estrategias de error para diferentes casos
   - Falta de categorización de errores

5. **Duplicación de Código**
   - `receive_message_aa()` y `receive_message_pp()` son casi idénticas

## 🏗️ Arquitectura Propuesta

### 📦 Estructura de Módulos

```
whatsapp_webhook/
├── __init__.py
├── message_types.py          # ✅ Ya existe - Tipos y estructuras de datos
├── logging_config.py         # 🆕 Nuevo - Configuración simple de logging
├── exceptions.py             # 🆕 Nuevo - Excepciones específicas
├── webhook/                  # 🆕 Nuevo - Handlers HTTP simples
│   ├── __init__.py
│   ├── main.py               # FastAPI app principal - simple y directo
│   └── auth.py               # Validación de webhooks
├── message_processing/       # 🆕 Nuevo - Procesamiento funcional
│   ├── __init__.py
│   ├── registry.py           # Registry global con decoradores
│   ├── parsers.py            # Parsers como funciones con @register_parser
│   ├── processors.py         # Processors como funciones con @register_processor
│   └── utils.py              # Funciones utilitarias (send_to_agent, etc.)
├── responses/                # 🆕 Nuevo - Builder simple para respuestas
│   ├── __init__.py
│   └── builder.py            # WhatsAppMessageBuilder simple
├── sessions.py               # ✅ Mantener - Manejo de sesiones
├── utils.py                  # ✅ Mantener - Utilidades generales
└── messages.py               # 🔄 DEPRECATED - Migrar a message_processing/
```

### 🎨 Patrones de Diseño Modernos con Python 3.12

#### 1. **Funciones Modulares** - Enfoque Pythónico Directo
```python
from typing import TypeAlias, Callable, Any
from functools import wraps
import asyncio
from contextlib import asynccontextmanager

# Type aliases simples y claros
MessageHandler: TypeAlias = Callable[[dict, str], dict[str, Any]]
MessageParser: TypeAlias = Callable[[dict], MessageData]
MessageProcessor: TypeAlias = Callable[[MessageData, dict], str]

# Registry global simple - pythónico
MESSAGE_PARSERS: dict[MessageType, MessageParser] = {}
MESSAGE_PROCESSORS: dict[MessageType, MessageProcessor] = {}

def register_parser(message_type: MessageType):
    """Decorator para registrar parsers - pythónico y simple."""
    def decorator(func: MessageParser) -> MessageParser:
        MESSAGE_PARSERS[message_type] = func
        return func
    return decorator

def register_processor(message_type: MessageType):
    """Decorator para registrar processors - pythónico y simple."""
    def decorator(func: MessageProcessor) -> MessageProcessor:
        MESSAGE_PROCESSORS[message_type] = func
        return func
    return decorator

# Función principal - directa y clara
async def process_webhook_message(
    raw_payload: dict,
    app_name: str,
    whatsapp_api_url: str,
    wsp_token: str,
    session_id: str | None = None
) -> dict[str, Any]:
    """
    Función principal para procesar mensajes de WhatsApp.
    
    Simple, directa y fácil de testear.
    """
    logger = get_logger("message_processing", {"app_name": app_name})
    
    try:
        # 1. Detectar tipo de mensaje usando pattern matching
        message_type = detect_message_type(raw_payload)
        logger.info(f"Detected message type: {message_type}")
        
        # 2. Parse del mensaje
        message_data = await parse_message(raw_payload, message_type)
        logger.debug(f"Parsed message data", extra={"message_id": message_data.message_id})
        
        # 3. Crear contexto
        context = {
            "app_name": app_name,
            "whatsapp_api_url": whatsapp_api_url,
            "wsp_token": wsp_token,
            "session_id": session_id or generate_session_id(message_data.user_wa_id),
            "user_wa_id": message_data.user_wa_id
        }
        
        # 4. Procesar mensaje
        response_text = await process_message(message_data, context)
        
        # 5. Enviar respuesta a WhatsApp
        await send_whatsapp_message(
            to=message_data.user_wa_id,
            message={"text": {"body": response_text}},
            whatsapp_api_url=whatsapp_api_url,
            token=wsp_token
        )
        
        logger.info("Message processed successfully")
        
        return {
            "status": "success",
            "message_id": message_data.message_id,
            "response": response_text
        }
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

def detect_message_type(raw_payload: dict) -> MessageType:
    """Detecta el tipo de mensaje usando pattern matching pythónico."""
    try:
        message = raw_payload["entry"][0]["changes"][0]["value"]["messages"][0]
        msg_type = message.get("type", "unknown")
        return MessageType.from_string(msg_type)
    except (KeyError, IndexError):
        return MessageType.UNSUPPORTED

async def parse_message(raw_payload: dict, message_type: MessageType) -> MessageData:
    """Parse del mensaje usando el parser registrado."""
    parser = MESSAGE_PARSERS.get(message_type, MESSAGE_PARSERS[MessageType.UNSUPPORTED])
    return parser(raw_payload)

async def process_message(message_data: MessageData, context: dict) -> str:
    """Procesa el mensaje usando el processor registrado."""
    processor = MESSAGE_PROCESSORS.get(
        message_data.message_type, 
        MESSAGE_PROCESSORS[MessageType.UNSUPPORTED]
    )
    return await processor(message_data, context)

# Ejemplo de parsers registrados - simple y claro
@register_parser(MessageType.TEXT)
def parse_text_message(raw_payload: dict) -> MessageData:
    """Parser para mensajes de texto."""
    message = raw_payload["entry"][0]["changes"][0]["value"]["messages"][0]
    
    return MessageData(
        message_id=message["id"],
        user_wa_id=message["from"],
        message_type=MessageType.TEXT,
        timestamp=message["timestamp"],
        text_content=message["text"]["body"]
    )

@register_parser(MessageType.IMAGE)
def parse_image_message(raw_payload: dict) -> MessageData:
    """Parser para mensajes de imagen."""
    message = raw_payload["entry"][0]["changes"][0]["value"]["messages"][0]
    image_data = message["image"]
    
    return MessageData(
        message_id=message["id"],
        user_wa_id=message["from"],
        message_type=MessageType.IMAGE,
        timestamp=message["timestamp"],
        media_id=image_data["id"],
        media_mime_type=image_data.get("mime_type"),
        media_caption=image_data.get("caption")
    )

@register_parser(MessageType.UNSUPPORTED)
def parse_unsupported_message(raw_payload: dict) -> MessageData:
    """Parser para mensajes no soportados."""
    message = raw_payload["entry"][0]["changes"][0]["value"]["messages"][0]
    
    return MessageData(
        message_id=message["id"],
        user_wa_id=message["from"],
        message_type=MessageType.UNSUPPORTED,
        timestamp=message["timestamp"],
        text_content="Tipo de mensaje no soportado"
    )

# Ejemplo de processors registrados - simple y directo
@register_processor(MessageType.TEXT)
async def process_text_message(message_data: MessageData, context: dict) -> str:
    """Procesa mensajes de texto enviándolos al agente."""
    logger = get_logger("text_processor", context)
    
    try:
        # Enviar al agente usando función simple
        agent_response = await send_to_agent(
            app_name=context["app_name"],
            user_id=message_data.user_wa_id,
            session_id=context["session_id"],
            message=message_data.text_content
        )
        
        return agent_response.get("response", "No pude procesar tu mensaje")
        
    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        return "Hubo un error procesando tu mensaje. Intenta de nuevo."

@register_processor(MessageType.IMAGE)
async def process_image_message(message_data: MessageData, context: dict) -> str:
    """Procesa mensajes de imagen."""
    logger = get_logger("image_processor", context)
    
    try:
        # Descargar imagen
        image_data = await download_whatsapp_media(
            media_id=message_data.media_id,
            whatsapp_api_url=context["whatsapp_api_url"],
            token=context["wsp_token"]
        )
        
        # Analizar imagen con IA (placeholder)
        analysis = await analyze_image_with_ai(
            image_data=image_data,
            caption=message_data.media_caption,
            app_name=context["app_name"]
        )
        
        # Enviar resultado al agente
        message_with_analysis = f"Imagen recibida. Análisis: {analysis}"
        if message_data.media_caption:
            message_with_analysis += f"\nCaption: {message_data.media_caption}"
        
        agent_response = await send_to_agent(
            app_name=context["app_name"],
            user_id=message_data.user_wa_id,
            session_id=context["session_id"],
            message=message_with_analysis
        )
        
        return agent_response.get("response", "Imagen procesada correctamente")
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return "No pude procesar la imagen. Intenta enviarla de nuevo."

@register_processor(MessageType.UNSUPPORTED)
async def process_unsupported_message(message_data: MessageData, context: dict) -> str:
    """Procesa mensajes no soportados."""
    return (
        "Este tipo de mensaje aún no está soportado. "
        "Por favor envía un mensaje de texto con tu consulta."
    )
```

#### 2. **Funciones Utilitarias** - Simples y Reutilizables
```python
import httpx
import json
from typing import Any, Optional

async def send_to_agent(
    app_name: str,
    user_id: str,
    session_id: str,
    message: str,
    agent_url: Optional[str] = None
) -> dict[str, Any]:
    """
    Envía mensaje al agente usando httpx - simple y directo.
    """
    agent_url = agent_url or get_agent_url()
    
    payload = {
        "app_name": app_name,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": message}]
        },
        "streaming": False
    }
    
    # Obtener token usando función existente
    id_token = await get_id_token(agent_url)
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{agent_url}/run",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def send_whatsapp_message(
    to: str,
    message: dict,
    whatsapp_api_url: str,
    token: str
) -> dict[str, Any]:
    """
    Envía mensaje a WhatsApp API - función simple y clara.
    """
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
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{whatsapp_api_url}/messages",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def download_whatsapp_media(
    media_id: str,
    whatsapp_api_url: str,
    token: str
) -> bytes:
    """
    Descarga media de WhatsApp - función directa.
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Obtener info del archivo
        media_response = await client.get(
            f"{whatsapp_api_url}/{media_id}",
            headers=headers
        )
        media_response.raise_for_status()
        media_info = media_response.json()
        
        # Descargar archivo
        file_response = await client.get(
            media_info["url"],
            headers=headers
        )
        file_response.raise_for_status()
        return file_response.content

async def analyze_image_with_ai(
    image_data: bytes,
    caption: Optional[str],
    app_name: str
) -> str:
    """
    Placeholder para análisis de imagen con IA.
    """
    # TODO: Implementar análisis real con servicio de IA
    analysis = "Imagen recibida y analizada"
    
    if caption:
        analysis += f" con descripción: {caption}"
    
    return analysis

def generate_session_id(user_wa_id: str) -> str:
    """Genera session ID simple basado en user ID."""
    import hashlib
    import time
    
    timestamp = str(int(time.time()))
    session_hash = hashlib.md5(f"{user_wa_id}_{timestamp}".encode()).hexdigest()
    return f"session_{session_hash[:8]}"

def get_agent_url() -> str:
    """Obtiene URL del agente desde variables de entorno."""
    import os
    return os.getenv("APP_URL", "")

async def get_id_token(target_url: str) -> str:
    """Obtiene token ID usando función existente."""
    from .utils import idtoken_from_metadata_server
    return idtoken_from_metadata_server(target_url)

def get_logger(name: str, context: dict = None) -> 'StructuredLogger':
    """Factory simple para loggers estructurados."""
    return StructuredLogger(name, context or {})
```

#### 3. **Webhook Handlers** - FastAPI Simple y Directo
```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import os

# Global app setup - simple y pythónico
app = FastAPI(title="WhatsApp Webhook", version="2.0.0")

async def handle_webhook_message(request: Request, app_name: str) -> JSONResponse:
    """
    Handler genérico para webhooks - simple y directo.
    """
    logger = get_logger("webhook", {"app_name": app_name})
    
    try:
        # 1. Obtener payload
        raw_payload = await request.json()
        logger.info("Webhook request received")
        
        # 2. Validar webhook de WhatsApp
        await validate_whatsapp_webhook(request)
        
        # 3. Obtener configuración de la app
        whatsapp_api_url = get_whatsapp_api_url(app_name)
        wsp_token = get_whatsapp_token(app_name)
        
        # 4. Procesar mensaje usando función principal
        result = await process_webhook_message(
            raw_payload=raw_payload,
            app_name=app_name,
            whatsapp_api_url=whatsapp_api_url,
            wsp_token=wsp_token
        )
        
        # 5. Respuesta basada en resultado
        if result["status"] == "success":
            logger.info("Message processed successfully")
            return JSONResponse(
                status_code=200,
                content={"status": "ok", "message_id": result.get("message_id")}
            )
        else:
            logger.error(f"Processing error: {result.get('error')}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "error": result.get("error")
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": "Internal server error"}
        )

# Routes específicos - simples y claros
@app.post("/webhook/aa")
async def receive_message_aa(request: Request):
    """Endpoint para mensajes de la app AA (Agricultura)."""
    return await handle_webhook_message(request, "AA")

@app.post("/webhook/pp")
async def receive_message_pp(request: Request):
    """Endpoint para mensajes de la app PP (Pesca)."""
    return await handle_webhook_message(request, "PP")

@app.get("/health")
async def health_check():
    """Health check simple."""
    return {"status": "healthy", "version": "2.0.0"}

@app.get("/status/{app_name}")
async def get_app_status(app_name: str):
    """Status de la aplicación específica."""
    supported_types = [t.value for t in MessageType if t != MessageType.UNSUPPORTED]
    
    return {
        "app_name": app_name,
        "supported_message_types": supported_types,
        "whatsapp_api_configured": bool(get_whatsapp_api_url(app_name)),
        "agent_url_configured": bool(get_agent_url())
    }

# Funciones de utilidad para webhook
async def validate_whatsapp_webhook(request: Request) -> None:
    """Valida autenticidad del webhook de WhatsApp."""
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    # TODO: Implementar validación real de signature
    # verify_webhook_signature(signature, request_body, webhook_secret)

def get_whatsapp_api_url(app_name: str) -> str:
    """Obtiene URL de WhatsApp API según la app."""
    match app_name.upper():
        case "AA":
            return os.getenv("WHATSAPP_API_URL_AA", "")
        case "PP":
            return os.getenv("WHATSAPP_API_URL_PP", "")
        case _:
            return os.getenv("WHATSAPP_API_URL_DEFAULT", "")

def get_whatsapp_token(app_name: str) -> str:
    """Obtiene token de WhatsApp según la app."""
    match app_name.upper():
        case "AA":
            return os.getenv("WHATSAPP_TOKEN_AA", "")
        case "PP":
            return os.getenv("WHATSAPP_TOKEN_PP", "")
        case _:
            return os.getenv("WHATSAPP_TOKEN_DEFAULT", "")

# Startup y shutdown simples
@app.on_event("startup")
async def startup_event():
    """Inicialización de la aplicación."""
    logger = get_logger("startup")
    logger.info("WhatsApp Webhook starting up")
    
    # Validar configuración básica
    required_env_vars = ["APP_URL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise RuntimeError(f"Missing environment variables: {missing_vars}")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar la aplicación."""
    logger = get_logger("shutdown")
    logger.info("WhatsApp Webhook shutting down")
```

#### 4. **Logging Estructurado Simple**
```python
import logging
import json
from typing import Any, Optional
from datetime import datetime
import os

class StructuredLogger:
    """Logger estructurado simple y pythónico."""
    
    def __init__(self, name: str, context: dict = None):
        self.name = name
        self.context = context or {}
        self.logger = logging.getLogger(f"whatsapp_webhook.{name}")
        self.is_debug = os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG"
        
        # Configurar handler si no existe
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, **kwargs):
        """Log info con contexto."""
        self._log(logging.INFO, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug - solo en modo debug."""
        if self.is_debug:
            self._log(logging.DEBUG, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error con información de excepción."""
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning."""
        self._log(logging.WARNING, message, **kwargs)
    
    def _log(self, level: int, message: str, exc_info: bool = False, **kwargs):
        """Log interno con contexto estructurado."""
        # Combinar contexto base con datos adicionales
        log_data = {**self.context, **kwargs}
        
        # Sanitizar datos sensibles
        sanitized_data = self._sanitize_data(log_data)
        
        # Agregar contexto al mensaje si hay datos
        if sanitized_data:
            extra_info = json.dumps(sanitized_data, default=str)
            full_message = f"{message} | Context: {extra_info}"
        else:
            full_message = message
        
        self.logger.log(level, full_message, exc_info=exc_info)
    
    def _sanitize_data(self, data: dict) -> dict:
        """Sanitizar datos sensibles en logs."""
        sensitive_keys = {"token", "password", "authorization", "secret", "key"}
        sanitized = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Verificar si es clave sensible
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            # Sanitizar user IDs en modo producción
            elif key_lower == "user_wa_id" and not self.is_debug and isinstance(value, str):
                if len(value) > 8:
                    sanitized[key] = f"{value[:4]}***{value[-4:]}"
                else:
                    sanitized[key] = "***"
            else:
                sanitized[key] = value
        
        return sanitized

# Configuración global de logging
def setup_logging():
    """Configurar logging global de la aplicación."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar loggers específicos
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)

# Call setup al importar
setup_logging()
```

#### 5. **Respuestas con Builder Simple**
```python
from typing import Optional, Any
from dataclasses import dataclass, field

@dataclass
class WhatsAppMessageBuilder:
    """Builder simple para mensajes de WhatsApp."""
    to: str = ""
    message_type: str = ""
    content: dict[str, Any] = field(default_factory=dict)
    
    def send_to(self, phone_number: str) -> 'WhatsAppMessageBuilder':
        """Configurar destinatario."""
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"
        self.to = phone_number
        return self
    
    def text(self, body: str, preview_url: bool = False) -> 'WhatsAppMessageBuilder':
        """Mensaje de texto simple."""
        self.message_type = "text"
        self.content = {
            "text": {
                "body": body,
                "preview_url": preview_url
            }
        }
        return self
    
    def image(self, media_id: str, caption: Optional[str] = None) -> 'WhatsAppMessageBuilder':
        """Mensaje de imagen."""
        self.message_type = "image"
        self.content = {
            "image": {
                "id": media_id,
                **({"caption": caption} if caption else {})
            }
        }
        return self
    
    def buttons(self, body: str, buttons: list[str]) -> 'WhatsAppMessageBuilder':
        """Mensaje con botones (máximo 3)."""
        if len(buttons) > 3:
            raise ValueError("Máximo 3 botones permitidos")
        
        self.message_type = "interactive"
        self.content = {
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"btn_{i}",
                                "title": button
                            }
                        }
                        for i, button in enumerate(buttons)
                    ]
                }
            }
        }
        return self
    
    def build(self) -> dict[str, Any]:
        """Construir mensaje final."""
        if not self.to:
            raise ValueError("Destinatario requerido")
        if not self.message_type:
            raise ValueError("Tipo de mensaje requerido")
        
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.to,
            "type": self.message_type,
            **self.content
        }

# Función helper para crear builder
def create_whatsapp_message() -> WhatsAppMessageBuilder:
    """Factory function para crear builder."""
    return WhatsAppMessageBuilder()

# Ejemplos de uso pythónico
async def send_welcome_message(user_wa_id: str, app_name: str):
    """Enviar mensaje de bienvenida con botones."""
    message = (
        create_whatsapp_message()
        .send_to(user_wa_id)
        .buttons(
            body=f"¡Bienvenido a {app_name}! ¿En qué puedo ayudarte?",
            buttons=["Consulta técnica", "Información general", "Hablar con experto"]
        )
        .build()
    )
    
    # Enviar usando función utilitaria
    return await send_whatsapp_message(
        to=user_wa_id,
        message=message,
        whatsapp_api_url=get_whatsapp_api_url(app_name),
        token=get_whatsapp_token(app_name)
    )

async def send_text_response(user_wa_id: str, text: str, app_name: str):
    """Enviar respuesta de texto simple."""
    message = (
        create_whatsapp_message()
        .send_to(user_wa_id)
        .text(text)
        .build()
    )
    
    return await send_whatsapp_message(
        to=user_wa_id,
        message=message,
        whatsapp_api_url=get_whatsapp_api_url(app_name),
        token=get_whatsapp_token(app_name)
    )
```

#### 4. **Observer Pattern** con Async/Await y Type Safety
```python
from typing import AsyncContextManager, AsyncGenerator
from contextlib import asynccontextmanager
import asyncio
from weakref import WeakSet

class MessageEvent:
    """Evento de mensaje con metadata."""
    def __init__(self, message_data: MessageData, context: ProcessingContext, result: ProcessingResult):
        self.message_data = message_data
        self.context = context
        self.result = result
        self.timestamp = datetime.utcnow()

class AsyncMessageObserver(Protocol):
    """Protocol para observadores asincrónicos."""
    async def on_message_received(self, event: MessageEvent) -> None: ...
    async def on_message_processed(self, event: MessageEvent) -> None: ...
    async def on_message_error(self, event: MessageEvent, error: Exception) -> None: ...

class MessageEventBus:
    """Event bus asincrónico con weak references."""
    
    def __init__(self):
        self._observers: WeakSet[AsyncMessageObserver] = WeakSet()
        self._event_queue: asyncio.Queue[MessageEvent] = asyncio.Queue()
        self._processing = False
    
    def subscribe(self, observer: AsyncMessageObserver) -> None:
        """Subscribe observer with automatic cleanup."""
        self._observers.add(observer)
    
    async def publish(self, event: MessageEvent) -> None:
        """Publish event to queue."""
        await self._event_queue.put(event)
    
    @asynccontextmanager
    async def processing_context(self) -> AsyncGenerator[None, None]:
        """Context manager for event processing."""
        if self._processing:
            raise RuntimeError("Event bus is already processing")
        
        self._processing = True
        processing_task = asyncio.create_task(self._process_events())
        
        try:
            yield
        finally:
            self._processing = False
            processing_task.cancel()
            try:
                await processing_task
            except asyncio.CancelledError:
                pass
    
    async def _process_events(self) -> None:
        """Process events from queue."""
        while self._processing:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._notify_observers(event)
            except asyncio.TimeoutError:
                continue
    
    async def _notify_observers(self, event: MessageEvent) -> None:
        """Notify all observers concurrently."""
        tasks = []
        for observer in self._observers:
            match event.result.success:
                case True:
                    tasks.append(observer.on_message_processed(event))
                case False:
                    tasks.append(observer.on_message_error(event, Exception("Processing failed")))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
```

#### 5. **Dependency Injection** con Context Managers
```python
from typing import TypeVar, Generic, ContextManager
from contextlib import contextmanager
import threading

ServiceType = TypeVar('ServiceType')

class ServiceContainer:
    """Dependency injection container thread-safe."""
    
    def __init__(self):
        self._services: dict[type, Any] = {}
        self._singletons: dict[type, Any] = {}
        self._lock = threading.RLock()
    
    def register_singleton(self, service_type: type[ServiceType], instance: ServiceType) -> None:
        """Register singleton service."""
        with self._lock:
            self._singletons[service_type] = instance
    
    def register_factory(self, service_type: type[ServiceType], factory: Callable[[], ServiceType]) -> None:
        """Register factory for service."""
        with self._lock:
            self._services[service_type] = factory
    
    def get(self, service_type: type[ServiceType]) -> ServiceType:
        """Get service instance."""
        with self._lock:
            # Check singletons first
            if service_type in self._singletons:
                return self._singletons[service_type]
            
            # Check factories
            if service_type in self._services:
                return self._services[service_type]()
            
            raise ValueError(f"Service {service_type} not registered")
    
    @contextmanager
    def scope(self) -> ContextManager['ServiceScope']:
        """Create scoped service container."""
        scope = ServiceScope(parent=self)
        try:
            yield scope
        finally:
            scope.dispose()

class ServiceScope:
    """Scoped service container."""
    
    def __init__(self, parent: ServiceContainer):
        self._parent = parent
        self._scoped_services: dict[type, Any] = {}
    
    def get(self, service_type: type[ServiceType]) -> ServiceType:
        """Get service from scope or parent."""
        if service_type in self._scoped_services:
            return self._scoped_services[service_type]
        
        instance = self._parent.get(service_type)
        self._scoped_services[service_type] = instance
        return instance
    
    def dispose(self) -> None:
        """Dispose scoped services."""
        for service in self._scoped_services.values():
            if hasattr(service, 'dispose'):
                service.dispose()
        self._scoped_services.clear()
```

### 🎨 Sistema de Logging Estructurado

#### **Niveles de Logging por Contexto**

```python
from enum import Enum
import logging
import os

class LogLevel(Enum):
    """Niveles de logging para diferentes contextos."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogContext(Enum):
    """Contextos de logging para categorización."""
    WEBHOOK = "webhook"
    MESSAGE_PARSING = "message_parsing"
    MESSAGE_PROCESSING = "message_processing"
    AGENT_COMMUNICATION = "agent_communication"
    WHATSAPP_API = "whatsapp_api"
    AUTHENTICATION = "authentication"
    PERFORMANCE = "performance"

# Configuración de logging por contexto
LOGGING_CONFIG = {
    LogContext.WEBHOOK: {
        "level": logging.INFO,
        "sensitive_data": False,  # No loggear payloads completos
    },
    LogContext.MESSAGE_PARSING: {
        "level": logging.INFO,
        "sensitive_data": True,   # Solo en DEBUG
    },
    LogContext.MESSAGE_PROCESSING: {
        "level": logging.INFO,
        "sensitive_data": True,   # Solo en DEBUG
    },
    LogContext.AGENT_COMMUNICATION: {
        "level": logging.INFO,
        "sensitive_data": True,   # Payloads y respuestas solo en DEBUG
    },
    LogContext.WHATSAPP_API: {
        "level": logging.INFO,
        "sensitive_data": True,   # Tokens y payloads solo en DEBUG
    },
    LogContext.AUTHENTICATION: {
        "level": logging.WARNING,
        "sensitive_data": True,   # Tokens nunca en logs
    },
    LogContext.PERFORMANCE: {
        "level": logging.INFO,
        "sensitive_data": False,
    }
}
```

#### **Implementación de Logger Estructurado**

```python
class StructuredLogger:
    """Logger estructurado con contexto y niveles dinámicos."""
    
    def __init__(self, context: LogContext):
        self.context = context
        self.logger = logging.getLogger(f"whatsapp_webhook.{context.value}")
        self.config = LOGGING_CONFIG[context]
        self.is_debug = os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG"
    
    def log_message_received(self, message_type: str, user_id: str, app_name: str, message_data: dict = None):
        """Log de mensaje recibido - datos sensibles solo en DEBUG."""
        self.logger.info(
            f"Message received",
            extra={
                "message_type": message_type,
                "user_id": self._sanitize_user_id(user_id),
                "app_name": app_name,
                "context": self.context.value
            }
        )
        
        # Datos completos del mensaje solo en DEBUG
        if self.is_debug and message_data:
            self.logger.debug(
                f"Full message data",
                extra={
                    "message_data": message_data,
                    "context": self.context.value
                }
            )
    
    def log_agent_request(self, user_id: str, app_name: str, payload: dict = None):
        """Log de request al agente - payload solo en DEBUG."""
        self.logger.info(
            f"Sending request to agent",
            extra={
                "user_id": self._sanitize_user_id(user_id),
                "app_name": app_name,
                "context": self.context.value
            }
        )
        
        if self.is_debug and payload:
            # Sanitizar payload para remover información sensible
            sanitized_payload = self._sanitize_payload(payload)
            self.logger.debug(
                f"Agent request payload",
                extra={
                    "payload": sanitized_payload,
                    "context": self.context.value
                }
            )
    
    def log_whatsapp_response(self, user_id: str, app_name: str, status_code: int, response_data: dict = None):
        """Log de respuesta de WhatsApp API."""
        self.logger.info(
            f"WhatsApp API response",
            extra={
                "user_id": self._sanitize_user_id(user_id),
                "app_name": app_name,
                "status_code": status_code,
                "context": self.context.value
            }
        )
        
        if self.is_debug and response_data:
            self.logger.debug(
                f"WhatsApp response data",
                extra={
                    "response_data": response_data,
                    "context": self.context.value
                }
            )
    
    def _sanitize_user_id(self, user_id: str) -> str:
        """Sanitizar ID de usuario para logs."""
        if not self.is_debug and len(user_id) > 8:
            return f"{user_id[:4]}***{user_id[-4:]}"
        return user_id
    
    def _sanitize_payload(self, payload: dict) -> dict:
        """Remover información sensible del payload."""
        sensitive_keys = ["token", "password", "secret", "authorization"]
        sanitized = payload.copy()
        
        for key in payload:
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
        
        return sanitized
```

#### **Enum para Tipos de Mensajes con Python 3.12 Features**

```python
from enum import Enum, auto, StrEnum
from typing import Self
from dataclasses import dataclass
import operator

class MessageType(StrEnum):  # Python 3.11+ StrEnum para mejor serialización
    """Tipos de mensajes soportados por WhatsApp Business API."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACTS = "contacts"
    INTERACTIVE = "interactive"
    REACTION = "reaction"
    TEMPLATE = "template"
    STICKER = "sticker"
    BUTTON = "button"
    LIST = "list"
    UNSUPPORTED = "unsupported"
    
    @classmethod
    def from_string(cls, message_type_str: str) -> Self:
        """Convertir string a MessageType con fallback usando pattern matching."""
        match message_type_str.lower().strip():
            case "text" | "txt":
                return cls.TEXT
            case "image" | "img" | "photo":
                return cls.IMAGE
            case "audio" | "voice" | "ptt":
                return cls.AUDIO
            case "video" | "vid":
                return cls.VIDEO
            case "document" | "doc" | "file":
                return cls.DOCUMENT
            case "location" | "loc" | "coordinates":
                return cls.LOCATION
            case "contacts" | "contact" | "vcard":
                return cls.CONTACTS
            case "interactive" | "button_reply" | "list_reply":
                return cls.INTERACTIVE
            case "reaction" | "emoji":
                return cls.REACTION
            case "template" | "hsm":
                return cls.TEMPLATE
            case "sticker":
                return cls.STICKER
            case _:
                return cls.UNSUPPORTED
    
    @property
    def requires_media_download(self) -> bool:
        """Indica si el tipo de mensaje requiere descarga de media."""
        return self in {self.IMAGE, self.AUDIO, self.VIDEO, self.DOCUMENT, self.STICKER}
    
    @property
    def supports_caption(self) -> bool:
        """Indica si el tipo de mensaje soporta caption."""
        return self in {self.IMAGE, self.VIDEO, self.DOCUMENT}
    
    @property
    def is_interactive(self) -> bool:
        """Indica si el mensaje es interactivo."""
        return self in {self.INTERACTIVE, self.BUTTON, self.LIST}
    
    @property
    def processing_priority(self) -> int:
        """Prioridad de procesamiento (1=alta, 5=baja)."""
        match self:
            case self.TEXT:
                return 1
            case self.INTERACTIVE | self.BUTTON | self.LIST:
                return 2
            case self.LOCATION | self.CONTACTS:
                return 3
            case self.IMAGE | self.AUDIO | self.VIDEO | self.DOCUMENT:
                return 4
            case _:
                return 5
    
    def get_max_size_mb(self) -> int | None:
        """Tamaño máximo permitido en MB según tipo."""
        match self:
            case self.IMAGE:
                return 5
            case self.AUDIO:
                return 16
            case self.VIDEO:
                return 16
            case self.DOCUMENT:
                return 100
            case self.STICKER:
                return 1
            case _:
                return None
    
    def __lt__(self, other: Self) -> bool:
        """Comparación por prioridad para sorting."""
        if not isinstance(other, MessageType):
            return NotImplemented
        return self.processing_priority < other.processing_priority

@dataclass(frozen=True, slots=True)
class MessageTypeInfo:
    """Información detallada sobre tipos de mensaje."""
    message_type: MessageType
    display_name: str
    description: str
    supported_mime_types: frozenset[str] = frozenset()
    max_size_mb: int | None = None
    requires_download: bool = False
    supports_caption: bool = False
    is_interactive: bool = False

# Registry de información de tipos usando pattern matching
MESSAGE_TYPE_REGISTRY: dict[MessageType, MessageTypeInfo] = {}

def register_message_type(message_type: MessageType) -> MessageTypeInfo:
    """Factory function para crear MessageTypeInfo usando pattern matching."""
    match message_type:
        case MessageType.TEXT:
            info = MessageTypeInfo(
                message_type=message_type,
                display_name="Texto",
                description="Mensaje de texto plano",
                max_size_mb=None,
                requires_download=False,
                supports_caption=False,
                is_interactive=False
            )
        
        case MessageType.IMAGE:
            info = MessageTypeInfo(
                message_type=message_type,
                display_name="Imagen",
                description="Imagen con caption opcional",
                supported_mime_types=frozenset(["image/jpeg", "image/png", "image/webp"]),
                max_size_mb=5,
                requires_download=True,
                supports_caption=True,
                is_interactive=False
            )
        
        case MessageType.AUDIO:
            info = MessageTypeInfo(
                message_type=message_type,
                display_name="Audio",
                description="Archivo de audio o nota de voz",
                supported_mime_types=frozenset(["audio/aac", "audio/mp4", "audio/mpeg", "audio/ogg"]),
                max_size_mb=16,
                requires_download=True,
                supports_caption=False,
                is_interactive=False
            )
        
        case MessageType.VIDEO:
            info = MessageTypeInfo(
                message_type=message_type,
                display_name="Video",
                description="Archivo de video con caption opcional",
                supported_mime_types=frozenset(["video/mp4", "video/3gpp"]),
                max_size_mb=16,
                requires_download=True,
                supports_caption=True,
                is_interactive=False
            )
        
        case MessageType.DOCUMENT:
            info = MessageTypeInfo(
                message_type=message_type,
                display_name="Documento",
                description="Archivo de documento",
                supported_mime_types=frozenset([
                    "application/pdf", "application/msword", 
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "text/plain", "text/csv"
                ]),
                max_size_mb=100,
                requires_download=True,
                supports_caption=True,
                is_interactive=False
            )
        
        case MessageType.LOCATION:
            info = MessageTypeInfo(
                message_type=message_type,
                display_name="Ubicación",
                description="Coordenadas de ubicación",
                max_size_mb=None,
                requires_download=False,
                supports_caption=False,
                is_interactive=False
            )
        
        case MessageType.INTERACTIVE:
            info = MessageTypeInfo(
                message_type=message_type,
                display_name="Interactivo",
                description="Mensaje con botones o lista",
                max_size_mb=None,
                requires_download=False,
                supports_caption=False,
                is_interactive=True
            )
        
        case _:
            info = MessageTypeInfo(
                message_type=message_type,
                display_name="No Soportado",
                description="Tipo de mensaje no soportado",
                max_size_mb=None,
                requires_download=False,
                supports_caption=False,
                is_interactive=False
            )
    
    MESSAGE_TYPE_REGISTRY[message_type] = info
    return info

# Inicializar registry
for msg_type in MessageType:
    register_message_type(msg_type)

class MessagePriority(Enum):
    """Prioridades de procesamiento con auto()."""
    CRITICAL = auto()  # Errores, autenticación
    HIGH = auto()      # Texto, interactivos
    MEDIUM = auto()    # Ubicación, contactos
    LOW = auto()       # Multimedia
    BACKGROUND = auto() # Reacciones, no soportados
    
    def __lt__(self, other: Self) -> bool:
        """Comparación para ordenamiento por prioridad."""
        if not isinstance(other, MessagePriority):
            return NotImplemented
        return self.value < other.value
```

## 📝 Tipos de Mensajes a Soportar

### 1. **Texto** ✅
- **Estado**: Implementado
- **Datos**: `body`
- **Respuesta**: Texto plano

### 2. **Imagen** 🆕
- **Datos**: `id`, `mime_type`, `sha256`, `caption`
- **Respuesta**: Texto descriptivo o imagen de respuesta
- **Casos de uso**: Análisis de imágenes de cultivos

### 3. **Audio** 🆕
- **Datos**: `id`, `mime_type`, `sha256`
- **Respuesta**: Transcripción + análisis
- **Casos de uso**: Consultas por voz

### 4. **Video** 🆕
- **Datos**: `id`, `mime_type`, `sha256`, `caption`
- **Respuesta**: Análisis de contenido
- **Casos de uso**: Videos de problemas en cultivos

### 5. **Documento** 🆕
- **Datos**: `id`, `mime_type`, `sha256`, `filename`, `caption`
- **Respuesta**: Análisis de documento
- **Casos de uso**: PDFs con reportes técnicos

### 6. **Ubicación** 🆕
- **Datos**: `latitude`, `longitude`, `name`, `address`
- **Respuesta**: Información contextual de la zona
- **Casos de uso**: Condiciones climáticas locales

### 7. **Contacto** 🆕
- **Datos**: `contacts[]` con `name`, `phones[]`
- **Respuesta**: Confirmación de recepción
- **Casos de uso**: Compartir contactos de expertos

### 8. **Interactivo** 🆕
- **Datos**: `type` (button_reply, list_reply), `button_reply`, `list_reply`
- **Respuesta**: Procesamiento de selección
- **Casos de uso**: Menús de opciones, formularios

### 9. **Reacción** 🆕
- **Datos**: `message_id`, `emoji`
- **Respuesta**: Acknowledgment
- **Casos de uso**: Feedback del usuario

## 🔧 Implementación por Fases

### **Fase 1: Refactor Base - Enfoque Pythónico** (Semana 1-2)
- [ ] Crear estructura de módulos simple (`webhook/`, `message_processing/`, `utils/`)
- [ ] Implementar función principal `process_webhook_message()` - directa y simple
- [ ] Crear registry global de parsers y processors usando decoradores
- [ ] Implementar parsers con decorador `@register_parser(MessageType)`
- [ ] Implementar processors con decorador `@register_processor(MessageType)`
- [ ] Crear funciones utilitarias simples (`send_to_agent`, `send_whatsapp_message`, `download_whatsapp_media`)
- [ ] Implementar FastAPI app directa sin dependency injection compleja
- [ ] Crear sistema de logging estructurado simple (`StructuredLogger`)
- [ ] Actualizar enum `MessageType` con StrEnum y métodos utilitarios
- [ ] Migrar funciones existentes usando enfoque funcional
- [ ] Tests simples usando funciones directas

### **Fase 2: Mensajes Multimedia - Funciones Simples** (Semana 3-4)
- [ ] Implementar parsers para multimedia usando decoradores `@register_parser`
- [ ] Implementar processors asincrónicos usando decoradores `@register_processor`
- [ ] Crear función `download_whatsapp_media()` simple y directa
- [ ] Implementar función `analyze_image_with_ai()` placeholder
- [ ] Crear `WhatsAppMessageBuilder` simple con fluent interface
- [ ] Tests para mensajes multimedia usando pytest-asyncio
- [ ] Actualizar handlers de FastAPI para soportar multimedia automáticamente

### **Fase 3: Mensajes Estructurados - Simples y Directos** (Semana 5-6)
- [ ] Implementar `@register_parser(MessageType.LOCATION)` para ubicaciones
- [ ] Implementar `@register_processor(MessageType.LOCATION)` con análisis de zona
- [ ] Implementar `@register_parser(MessageType.CONTACTS)` para contactos
- [ ] Implementar `@register_processor(MessageType.CONTACTS)` con confirmación
- [ ] Implementar `@register_parser(MessageType.INTERACTIVE)` para botones/listas
- [ ] Implementar `@register_processor(MessageType.INTERACTIVE)` con manejo de selecciones
- [ ] Tests simples para mensajes estructurados

### **Fase 4: Respuestas Enriquecidas - Builder Simple** (Semana 7-8)
- [ ] Extender `WhatsAppMessageBuilder` con más tipos de mensajes
- [ ] Implementar soporte para templates de WhatsApp
- [ ] Crear funciones helper para respuestas comunes (`send_welcome_message`, `send_text_response`)
- [ ] Implementar respuestas con botones usando builder
- [ ] Tests end-to-end con builder pattern

### **Fase 5: Optimización Simple** (Semana 9-10)
- [ ] Agregar métricas simples usando contadores globales
- [ ] Implementar cache simple para sesiones frecuentes
- [ ] Crear middleware simple para rate limiting
- [ ] Documentación pythónica con docstrings detallados
- [ ] Tests de performance con pytest-benchmark

## 🧪 Estrategia de Testing

### **Tests Simples y Pythónicos**
```python
import pytest
from unittest.mock import patch, AsyncMock
import asyncio

# Test de la función principal - directo y simple
@pytest.mark.asyncio
async def test_process_webhook_message():
    """Test de la función principal de procesamiento."""
    # Mock de las funciones utilitarias
    with patch('webhook_app.send_to_agent') as mock_agent, \
         patch('webhook_app.send_whatsapp_message') as mock_whatsapp:
        
        mock_agent.return_value = {"response": "Respuesta del agente"}
        mock_whatsapp.return_value = {"id": "msg_123"}
        
        # Test data
        raw_payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "id": "msg_123",
                                        "from": "1234567890",
                                        "type": "text",
                                        "timestamp": "1234567890",
                                        "text": {"body": "Hola agricultura"}
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        
        # Execute
        result = await process_webhook_message(
            raw_payload=raw_payload,
            app_name="AA",
            whatsapp_api_url="https://api.whatsapp.com",
            wsp_token="test_token"
        )
        
        # Verify
        assert result["status"] == "success"
        assert result["message_id"] == "msg_123"
        mock_agent.assert_called_once()
        mock_whatsapp.assert_called_once()

# Test de parsers usando registry
def test_text_message_parser():
    """Test del parser de mensajes de texto."""
    raw_payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "msg_123",
                                    "from": "1234567890",
                                    "type": "text",
                                    "timestamp": "1234567890",
                                    "text": {"body": "Mensaje de prueba"}
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    
    # Test usando función del registry
    parser = MESSAGE_PARSERS[MessageType.TEXT]
    message_data = parser(raw_payload)
    
    assert message_data.message_id == "msg_123"
    assert message_data.user_wa_id == "1234567890"
    assert message_data.text_content == "Mensaje de prueba"
    assert message_data.message_type == MessageType.TEXT

# Test de processors usando registry
@pytest.mark.asyncio
async def test_text_message_processor():
    """Test del processor de mensajes de texto."""
    message_data = MessageData(
        message_id="msg_123",
        user_wa_id="1234567890",
        message_type=MessageType.TEXT,
        timestamp="1234567890",
        text_content="Consulta sobre agricultura"
    )
    
    context = {
        "app_name": "AA",
        "session_id": "session_123",
        "user_wa_id": "1234567890"
    }
    
    with patch('webhook_app.send_to_agent') as mock_agent:
        mock_agent.return_value = {"response": "Respuesta sobre agricultura"}
        
        # Test usando función del registry
        processor = MESSAGE_PROCESSORS[MessageType.TEXT]
        result = await processor(message_data, context)
        
        assert result == "Respuesta sobre agricultura"
        mock_agent.assert_called_once_with(
            app_name="AA",
            user_id="1234567890",
            session_id="session_123",
            message="Consulta sobre agricultura"
        )

# Test del builder pattern
def test_whatsapp_message_builder():
    """Test del builder de mensajes de WhatsApp."""
    message = (
        create_whatsapp_message()
        .send_to("1234567890")
        .text("Mensaje de prueba")
        .build()
    )
    
    expected = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "+1234567890",
        "type": "text",
        "text": {
            "body": "Mensaje de prueba",
            "preview_url": False
        }
    }
    
    assert message == expected

def test_whatsapp_message_builder_buttons():
    """Test del builder con botones."""
    message = (
        create_whatsapp_message()
        .send_to("1234567890")
        .buttons("¿En qué puedo ayudarte?", ["Consulta", "Info", "Experto"])
        .build()
    )
    
    assert message["type"] == "interactive"
    assert message["interactive"]["type"] == "button"
    assert len(message["interactive"]["action"]["buttons"]) == 3

# Test de FastAPI endpoints
@pytest.mark.asyncio
async def test_webhook_aa_endpoint():
    """Test del endpoint de webhook AA."""
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    with patch('webhook_app.process_webhook_message') as mock_process:
        mock_process.return_value = {
            "status": "success",
            "message_id": "msg_123"
        }
        
        response = client.post(
            "/webhook/aa",
            json={"entry": [{"changes": [{"value": {"messages": [{}]}}]}]}
        )
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "message_id": "msg_123"}

# Test de logging estructurado
def test_structured_logger():
    """Test del logger estructurado."""
    logger = StructuredLogger("test", {"app_name": "AA"})
    
    with patch.object(logger.logger, 'info') as mock_log:
        logger.info("Test message", user_id="1234567890")
        
        # Verificar que se llamó con contexto
        mock_log.assert_called_once()
        call_args = mock_log.call_args[0][0]
        assert "Test message" in call_args
        assert "app_name" in call_args

# Test de detección de tipo de mensaje
def test_message_type_detection():
    """Test de pattern matching para detección de tipos."""
    test_cases = [
        ({"entry": [{"changes": [{"value": {"messages": [{"type": "text"}]}}]}]}, MessageType.TEXT),
        ({"entry": [{"changes": [{"value": {"messages": [{"type": "image"}]}}]}]}, MessageType.IMAGE),
        ({"entry": [{"changes": [{"value": {"messages": [{"type": "location"}]}}]}]}, MessageType.LOCATION),
        ({"entry": [{"changes": [{"value": {"messages": [{"type": "unknown"}]}}]}]}, MessageType.UNSUPPORTED),
        ({}, MessageType.UNSUPPORTED)
    ]
    
    for payload, expected_type in test_cases:
        detected_type = detect_message_type(payload)
        assert detected_type == expected_type

# Test de funciones utilitarias
@pytest.mark.asyncio
async def test_send_to_agent():
    """Test de envío al agente."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"response": "Test response"}
        mock_response.raise_for_status.return_value = None
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        with patch('webhook_app.get_id_token', return_value="test_token"):
            result = await send_to_agent(
                app_name="AA",
                user_id="1234567890",
                session_id="session_123",
                message="Test message"
            )
            
            assert result == {"response": "Test response"}

@pytest.mark.asyncio
async def test_send_whatsapp_message():
    """Test de envío a WhatsApp."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"id": "msg_123"}
        mock_response.raise_for_status.return_value = None
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        result = await send_whatsapp_message(
            to="1234567890",
            message={"text": {"body": "Test"}},
            whatsapp_api_url="https://api.whatsapp.com",
            token="test_token"
        )
        
        assert result == {"id": "msg_123"}
```

### **Tests Unitarios con Python 3.12 Features**
```python
import pytest
from unittest.mock import patch, AsyncMock
from typing import assert_type
import asyncio

# Test del facade pattern
@pytest.mark.asyncio
async def test_message_processor_facade():
    """Test de la abstracción principal del facade."""
    container = ServiceContainer()
    
    # Mock services
    mock_coordinator = AsyncMock(spec=MessageProcessingCoordinator)
    container.register_singleton(MessageProcessingCoordinator, mock_coordinator)
    
    facade = MessageProcessorFacade(container)
    
    # Test data
    raw_payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "id": "test_msg_123",
                        "from": "1234567890",
                        "type": "text",
                        "text": {"body": "Hola agricultura"}
                    }]
                }
            }]
        }]
    }
    
    webhook_context = {
        "whatsapp_api_url": "https://api.whatsapp.com",
        "wsp_token": "token123",
        "session_id": "session123"
    }
    
    # Configure mocks
    mock_message_data = MessageData("test_msg_123", "1234567890", MessageType.TEXT, text_content="Hola agricultura")
    mock_result = ProcessingResult(True, "Respuesta del agente", {})
    
    mock_coordinator.parse_message.return_value = mock_message_data
    mock_coordinator.process_message.return_value = mock_result
    mock_coordinator.generate_response.return_value = {"text": {"body": "Respuesta del agente"}}
    
    # Execute
    result = await facade.process_webhook_message(raw_payload, "AA", webhook_context)
    
    # Assertions
    assert result["status"] == "success"
    assert result["message_id"] == "test_msg_123"
    mock_coordinator.parse_message.assert_called_once_with(raw_payload)
    mock_coordinator.process_message.assert_called_once()

# Test de webhook handlers
@pytest.mark.asyncio
async def test_webhook_handlers_separation():
    """Test separación de responsabilidades en webhook handlers."""
    mock_facade = AsyncMock(spec=MessageProcessorFacade)
    handlers = WebhookHandlers(mock_facade)
    
    # Mock FastAPI request
    mock_request = AsyncMock()
    mock_request.json.return_value = {"test": "payload"}
    
    # Configure facade response
    mock_facade.process_webhook_message.return_value = {
        "status": "success",
        "message_id": "test123"
    }
    
    # Execute
    with patch.object(handlers, '_validate_webhook', return_value=None):
        with patch.object(handlers, '_get_whatsapp_api_url', return_value="https://api.whatsapp.com"):
            with patch.object(handlers, '_get_whatsapp_token', return_value="token123"):
                response = await handlers.receive_message_aa(mock_request)
    
    # Assertions
    assert response.status_code == 200
    assert response.body is not None
    mock_facade.process_webhook_message.assert_called_once()

# Test con pattern matching y type checking
def test_message_type_pattern_matching():
    """Test pattern matching en MessageType."""
    message_type = MessageType.from_string("img")
    assert message_type == MessageType.IMAGE
    
    # Type checking estático
    assert_type(message_type, MessageType)
    
    # Test pattern matching en processing
    match message_type:
        case MessageType.IMAGE | MessageType.VIDEO:
            assert message_type.requires_media_download
        case _:
            pytest.fail("Pattern matching failed")

# Test con generics y protocols
def test_abstract_factory_with_generics():
    """Test factory con type safety."""
    @AbstractMessageFactory.register_parser(MessageType.TEXT)
    class TestTextParser(BaseMessageParser):
        def parse(self, raw_message: dict, user_id: str) -> MessageData:
            return MessageData(
                message_id="test",
                user_wa_id=user_id,
                message_type=MessageType.TEXT,
                text_content=raw_message["text"]["body"]
            )
        
        def validate(self, raw_message: dict) -> bool:
            return "text" in raw_message
    
    parser = AbstractMessageFactory.create_parser(MessageType.TEXT)
    assert isinstance(parser, TestTextParser)
    assert_type(parser, BaseMessageParser)

# Test de external service clients
@pytest.mark.asyncio
async def test_agent_client():
    """Test cliente de agente con dependency injection."""
    client = ExternalServiceClients.AgentClient(
        base_url="https://agent.example.com"
    )
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = [{"content": "Respuesta del agente"}]
        mock_response.raise_for_status.return_value = None
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        with patch.object(client, '_get_id_token', return_value="token123"):
            result = await client.send_message("AA", "user123", "session123", "Hola")
        
        assert result == [{"content": "Respuesta del agente"}]

# Test asincrónico con event bus
@pytest.mark.asyncio
async def test_async_event_bus():
    """Test event bus asincrónico."""
    event_bus = MessageEventBus()
    events_received = []
    
    class TestObserver:
        async def on_message_received(self, event: MessageEvent) -> None:
            events_received.append(("received", event))
        
        async def on_message_processed(self, event: MessageEvent) -> None:
            events_received.append(("processed", event))
        
        async def on_message_error(self, event: MessageEvent, error: Exception) -> None:
            events_received.append(("error", event, error))
    
    observer = TestObserver()
    event_bus.subscribe(observer)
    
    test_event = MessageEvent(
        message_data=MessageData("test", "user123", MessageType.TEXT),
        context=ProcessingContext("test_app", "", "", "user123", "session123"),
        result=ProcessingResult(True, "Test response")
    )
    
    async with event_bus.processing_context():
        await event_bus.publish(test_event)
        await asyncio.sleep(0.1)  # Allow processing
    
    assert len(events_received) == 1
    assert events_received[0][0] == "processed"

# Test dependency injection con context manager
def test_service_container_with_scope():
    """Test service container con scoped services."""
    container = ServiceContainer()
    
    class TestService:
        def __init__(self):
            self.value = "test"
        
        def dispose(self):
            self.value = "disposed"
    
    container.register_factory(TestService, TestService)
    
    with container.scope() as scope:
        service1 = scope.get(TestService)
        service2 = scope.get(TestService)
        
        # Same instance within scope
        assert service1 is service2
        assert service1.value == "test"
    
    # Service should be disposed after scope
    assert service1.value == "disposed"

# Test builder pattern con fluent interface
def test_whatsapp_builder_fluent_interface():
    """Test builder con type safety y fluent interface."""
    message = (WhatsAppResponseBuilder()
               .to("+1234567890")
               .with_text("Hello World", preview_url=True)
               .build())
    
    expected = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual", 
        "to": "+1234567890",
        "type": "text",
        "text": {
            "body": "Hello World",
            "preview_url": True
        }
    }
    
    assert message == expected

# Test template builder
def test_template_builder_chain():
    """Test template builder con method chaining."""
    message = (WhatsAppResponseBuilder()
               .to("+1234567890")
               .with_template("welcome_message", "es")
               .with_header_parameter("Juan")
               .with_body_parameters("Agricultura", "2024")
               .build())
    
    assert message["type"] == "template"
    assert message["template"]["name"] == "welcome_message"
    assert len(message["template"]["components"]) == 2

# Test con exception groups (Python 3.11+)
def test_exception_groups():
    """Test manejo de múltiples errores."""
    errors = []
    
    try:
        # Simular múltiples errores de procesamiento
        raise ExceptionGroup("Processing errors", [
            MessageParsingError("Invalid JSON"),
            MessageProcessingError("Agent timeout"),
            UnsupportedMessageTypeError("Unknown type")
        ])
    except* MessageParsingError as eg:
        errors.extend(eg.exceptions)
    except* MessageProcessingError as eg:
        errors.extend(eg.exceptions)
    except* UnsupportedMessageTypeError as eg:
        errors.extend(eg.exceptions)
    
    assert len(errors) == 3
    assert any(isinstance(e, MessageParsingError) for e in errors)

# Test performance con slots
def test_dataclass_performance():
    """Test performance de dataclasses con slots."""
    import sys
    
    # MessageData usa slots=True para mejor performance
    message = MessageData(
        message_id="test",
        user_wa_id="user123",
        message_type=MessageType.TEXT,
        text_content="Hello"
    )
    
    # Slots reduce memory usage
    assert not hasattr(message, '__dict__')
    assert hasattr(message, '__slots__')
    
    # Should be smaller than regular class
    regular_size = sys.getsizeof(type('Regular', (), {'a': 1, 'b': 2, 'c': 3, 'd': 4})())
    slots_size = sys.getsizeof(message)
    assert slots_size < regular_size

# Test integración completa
@pytest.mark.asyncio
async def test_full_integration():
    """Test de integración completa webhook -> facade -> coordinador."""
    # Setup
    container = ServiceContainer()
    
    # Register services
    container.register_singleton(MessageProcessingCoordinator, MessageProcessingCoordinator(container))
    facade = MessageProcessorFacade(container)
    handlers = WebhookHandlers(facade)
    
    # Mock external dependencies
    with patch('whatsapp_webhook.external_services.agent_client.AgentClient') as mock_agent:
        with patch('whatsapp_webhook.external_services.whatsapp_client.WhatsAppClient') as mock_whatsapp:
            
            # Test payload
            mock_request = AsyncMock()
            mock_request.json.return_value = {
                "entry": [{
                    "changes": [{
                        "value": {
                            "messages": [{
                                "id": "msg123",
                                "from": "1234567890",
                                "type": "text",
                                "text": {"body": "¿Como combatir plagas en tomate?"}
                            }]
                        }
                    }]
                }]
            }
            
            # Execute full flow
            with patch.object(handlers, '_validate_webhook'):
                response = await handlers.receive_message_aa(mock_request)
            
            # Verify response
            assert response.status_code == 200
```

### **Tests de Integración**
- Simulación de webhooks completos de WhatsApp
- Tests con diferentes tipos de mensajes
- Validación de respuestas generadas

### **Tests de Performance**
- Benchmarks para diferentes volúmenes de mensajes
- Tests de concurrencia
- Medición de latencia por tipo de mensaje

## 📊 Métricas y Monitoring

### **Métricas Clave**
- Mensajes procesados por tipo
- Tiempo de respuesta por tipo
- Tasa de errores por tipo
- Uso de recursos por procesador
- **Logs por nivel de severidad**
- **Frecuencia de mensajes con datos sensibles**
- **Performance del sistema de logging**

### **Alertas**
- Tasa de errores > 5%
- Latencia > 10 segundos
- Mensajes no soportados > 1%
- **Logs de ERROR/CRITICAL acumulados**
- **Fallos en sanitización de datos sensibles**

## 🔄 Plan de Migración

### **Estrategia de Despliegue**
1. **Despliegue Blue-Green**: Mantener versión actual mientras se desarrolla la nueva
2. **Feature Flags**: Habilitar nuevos tipos de mensajes gradualmente
3. **Rollback Plan**: Capacidad de volver a la versión anterior rápidamente

### **Validación**
- Tests A/B entre versión actual y nueva
- Monitoreo de métricas de performance
- Feedback de usuarios en entorno de staging

## 🎯 Criterios de Éxito

### **Técnicos**
- [ ] Soporte para al menos 8 tipos de mensajes
- [ ] Cobertura de tests > 90%
- [ ] Tiempo de respuesta < 5 segundos para el 95% de mensajes
- [ ] Tasa de errores < 1%
- [ ] **Uso de Python 3.12 features (pattern matching, type aliases, StrEnum)**
- [ ] **Type safety con mypy score > 95%**
- [ ] **Memory efficiency con dataclasses slots**
- [ ] **Async processing para multimedia con rendimiento < 3s**

### **Funcionales**
- [ ] Usuarios pueden enviar imágenes y recibir análisis
- [ ] Soporte para ubicaciones con información contextual
- [ ] Menús interactivos funcionando correctamente
- [ ] Procesamiento de documentos básico
- [ ] **Builder pattern para respuestas complejas**
- [ ] **Event-driven architecture para notificaciones**

### **No Funcionales**
- [ ] Código mantenible con arquitectura clara
- [ ] Documentación completa para desarrolladores
- [ ] Logs estructurados para debugging
- [ ] Monitoring y alertas operacionales
- [ ] **Sistema de logging con diferentes niveles configurables**
- [ ] **Sanitización automática de datos sensibles en logs**
- [ ] **Compliance con políticas de privacidad en logging**
- [ ] **Dependency injection para testabilidad**
- [ ] **Async/await para operaciones I/O intensivas**
- [ ] **Pattern matching para control de flujo limpio**

## 🚀 Próximos Pasos

1. **Validación del Plan**: Revisar con el equipo técnico
2. **Estimación Detallada**: Refinamiento de tiempos por fase
3. **Setup del Entorno**: Configuración de herramientas de desarrollo
4. **Kick-off**: Inicio de la Fase 1

---

## 📚 Referencias

- [WhatsApp Business API - Message Types](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples)
- [Python Design Patterns](https://python-patterns.guide/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [Structured Logging Guidelines](https://structlog.org/)
- [GDPR Compliance for Logging](https://gdpr.eu/data-protection-impact-assessment-template/)
- **[Python 3.12 What's New](https://docs.python.org/3.12/whatsnew/3.12.html)**
- **[Python 3.11 Pattern Matching](https://docs.python.org/3/whatsnew/3.10.html#pep-634-structural-pattern-matching)**
- **[Python 3.11 Exception Groups](https://docs.python.org/3/whatsnew/3.11.html#pep-654-exception-groups-and-except)**
- **[Python Typing Best Practices](https://typing.readthedocs.io/en/latest/)**
- **[Modern Python Features Guide](https://realpython.com/python312-new-features/)**
- **[Async Python Patterns](https://docs.python.org/3/library/asyncio.html)**

---

**Documento creado**: 29 de julio, 2025  
**Autor**: GitHub Copilot  
**Versión**: 2.0  
**Estado**: Draft para revisión - **Actualizado con Python 3.12 Features**
