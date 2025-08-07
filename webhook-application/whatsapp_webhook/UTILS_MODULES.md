# 📦 Módulos de Utilidades WhatsApp Webhook

Este documento describe la nueva estructura modular de utilidades para la aplicación webhook de WhatsApp, organizada por responsabilidades específicas.

## 🗂️ Estructura de Módulos

```
whatsapp_webhook/
├── auth/                    # 🔐 Autenticación
│   ├── __init__.py
│   └── google_auth.py      # Autenticación con Google Cloud
├── external_services/       # 🌐 Servicios externos
│   ├── __init__.py
│   ├── agent_client.py     # Cliente para el servicio de agente IA
│   └── whatsapp_client.py  # Cliente para WhatsApp Business API
├── utils/                   # 🛠️ Utilidades generales
│   ├── __init__.py
│   ├── config.py           # Configuración y variables de entorno
│   ├── helpers.py          # Funciones de ayuda generales
│   └── logging.py          # Sistema de logging estructurado
└── utils.py                # 🚨 DEPRECATED - Solo para compatibilidad
```

## 📋 Descripción de Módulos

### 🔐 `auth/` - Autenticación
Funciones relacionadas con autenticación y tokens de acceso.

**Módulos:**
- `google_auth.py`: Autenticación con Google Cloud metadata server

**Funciones principales:**
- `idtoken_from_metadata_server(url)`: Obtiene token ID desde metadata server
- `get_id_token(target_url)`: Wrapper async para obtener token ID

### 🌐 `external_services/` - Servicios Externos
Clientes para comunicación con APIs externas.

**Módulos:**
- `agent_client.py`: Comunicación con el servicio de agente IA
- `whatsapp_client.py`: Comunicación básica con WhatsApp Business API
- `whatsapp_actions.py`: Acciones específicas de WhatsApp (typing, mark_seen)
- `whatsapp_enhanced.py`: Funcionalidad mejorada de UX para WhatsApp

**Funciones principales:**
- `send_to_agent()`: Envía mensaje al agente IA
- `send_whatsapp_message()`: Envía mensaje a WhatsApp
- `download_whatsapp_media()`: Descarga archivos multimedia
- `create_text_message()`, `create_image_message()`: Creadores de mensajes
- `send_typing_indicator()`: Muestra indicador de escritura
- `mark_message_as_read()`: Marca mensajes como leídos
- `ConversationManager`: Gestión avanzada de conversaciones con UX mejorada

### 🛠️ `utils/` - Utilidades Generales
Funciones de ayuda, configuración y logging.

**Módulos:**
- `config.py`: Manejo de configuración y variables de entorno
- `helpers.py`: Funciones de utilidad general
- `logging.py`: Sistema de logging estructurado

**Funciones principales:**
- `get_whatsapp_api_url()`, `get_whatsapp_token()`: Configuración por aplicación
- `validate_phone_number()`, `sanitize_user_id()`: Validación y sanitización
- `get_logger()`: Factory para crear loggers estructurados

## 🔄 Migración desde `utils.py`

El archivo original `utils.py` ha sido descompuesto de la siguiente manera:

| Función Original | Nuevo Módulo | Nuevo Archivo |
|------------------|--------------|---------------|
| `idtoken_from_metadata_server()` | `auth` | `google_auth.py` |
| Funciones de agente | `external_services` | `agent_client.py` |
| Funciones de WhatsApp | `external_services` | `whatsapp_client.py` |
| Configuración | `utils` | `config.py` |
| Helpers generales | `utils` | `helpers.py` |
| Logging | `utils` | `logging.py` |

## 📖 Ejemplos de Uso

### Autenticación
```python
from whatsapp_webhook.auth.google_auth import get_id_token

# Obtener token para autenticación
token = await get_id_token("https://api.example.com")
```

### Cliente de Agente
```python
from whatsapp_webhook.external_services.agent_client import send_to_agent

# Enviar mensaje al agente
response = await send_to_agent(
    app_name="AA",
    user_id="1234567890",
    session_id="session123",
    message="¿Cómo combatir plagas?"
)
```

### Cliente de WhatsApp
```python
from whatsapp_webhook.external_services.whatsapp_client import (
    send_whatsapp_message, 
    create_text_message
)

# Crear y enviar mensaje de texto
message = create_text_message("¡Hola! ¿En qué puedo ayudarte?")
result = await send_whatsapp_message(
    to="+1234567890",
    message=message,
    whatsapp_api_url="https://api.whatsapp.com",
    token="your_token"
)
```

### Configuración
```python
from whatsapp_webhook.utils.app_config import config

# Obtener URL específica por aplicación
url = get_whatsapp_api_url("AA")

# Validar configuración
missing_vars = validate_environment_config("AA")
if missing_vars:
    print(f"Variables faltantes: {missing_vars}")
```

### Logging Estructurado
```python
from whatsapp_webhook.utils.logging import get_logger

# Crear logger con contexto
logger = get_logger("webhook", {"app_name": "AA"})

# Logs estructurados
logger.info("Message received", extra={"user_id": "123", "message_type": "text"})
logger.log_message_received("text", "123", "AA", {"content": "hola"})
```

### Helpers
```python
from whatsapp_webhook.utils.helpers import (
    validate_phone_number,
    normalize_phone_number,
    sanitize_user_id
)

# Validar y normalizar número
if validate_phone_number("1234567890"):
    phone = normalize_phone_number("1234567890")  # "+1234567890"

# Sanitizar para logging
safe_id = sanitize_user_id("1234567890")  # "12****90"
```

## 🚨 Deprecación

El archivo `utils.py` original sigue funcionando por compatibilidad hacia atrás, pero emite un `DeprecationWarning`. Se recomienda migrar a los nuevos módulos específicos:

```python
# ❌ Obsoleto (funciona pero deprecated)
from whatsapp_webhook.utils import idtoken_from_metadata_server

# ✅ Nuevo enfoque recomendado
from whatsapp_webhook.auth.google_auth import idtoken_from_metadata_server
```

## 🎯 Beneficios de la Modularización

1. **Separación de responsabilidades**: Cada módulo tiene una función específica
2. **Reutilización**: Funciones más granulares y reutilizables
3. **Mantenibilidad**: Código más fácil de mantener y testear
4. **Escalabilidad**: Fácil agregar nuevas funcionalidades sin romper código existente
5. **Testing**: Cada módulo se puede testear independientemente
6. **Documentación**: Código más autodocumentado y organizado

## 🔗 Importaciones Recomendadas

Para facilitar el uso, puedes importar desde los paquetes principales:

```python
# Autenticación
from whatsapp_webhook.auth import idtoken_from_metadata_server

# Servicios externos
from whatsapp_webhook.external_services import (
    send_to_agent, 
    send_whatsapp_message, 
    download_whatsapp_media
)

# Utilidades
from whatsapp_webhook.utils import (
    get_logger,
    get_whatsapp_api_url,
    validate_phone_number
)
```
