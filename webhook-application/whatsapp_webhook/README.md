# WhatsApp Webhook - Estructura Modular

## 📦 Estructura Actualizada

El proyecto se ha reorganizado siguiendo un enfoque más pythónico y modular:

```
whatsapp_webhook/
├── __init__.py
├── message_types.py          # ✅ Tipos y estructuras de datos
├── auth/                     # 🆕 Autenticación
│   ├── __init__.py
│   └── google_auth.py        # Autenticación con Google Cloud
├── external_services/        # 🆕 Servicios externos
│   ├── __init__.py
│   ├── agent_client.py       # Cliente del servicio de agentes
│   └── whatsapp_client.py    # Cliente de WhatsApp API
├── utils/                    # 🆕 Utilidades generales
│   ├── __init__.py
│   ├── helpers.py            # Funciones auxiliares
│   ├── config.py             # Configuración y variables de entorno
│   └── logging.py            # Sistema de logging estructurado
├── sessions.py               # ✅ Manejo de sesiones (actualizado)
├── messages.py               # 🔄 Procesamiento de mensajes (actualizado)
└── utils.py                  # ⚠️ DEPRECATED - usar módulos específicos
```

## 🔄 Cambios Principales

### 1. **Descomposición de `utils.py`**

El archivo monolítico `utils.py` se ha dividido en módulos específicos:

- **`auth/google_auth.py`**: Funciones de autenticación con Google Cloud
- **`external_services/agent_client.py`**: Comunicación con el servicio de agentes
- **`external_services/whatsapp_client.py`**: Comunicación con WhatsApp API
- **`utils/helpers.py`**: Funciones auxiliares generales
- **`utils/config.py`**: Gestión de configuración y variables de entorno
- **`utils/logging.py`**: Sistema de logging estructurado

### 2. **Sistema de Logging Mejorado**

```python
from whatsapp_webhook.utils.logging import get_logger

# Crear logger con contexto
logger = get_logger("message_processing", {"app_name": "AA"})

# Usar métodos específicos para diferentes tipos de log
logger.log_message_received("text", user_id, app_name, message_data)
logger.log_agent_request(user_id, app_name, payload)
logger.log_whatsapp_response(user_id, app_name, status_code, response_data)
```

### 3. **Funciones de Configuración**

```python
from whatsapp_webhook.utils.app_config import config

# Obtener configuración específica por app
api_url = get_whatsapp_api_url("AA")
token = get_whatsapp_token("AA")

# Validar configuración
missing_vars = validate_environment_config("AA")
if missing_vars:
    raise ValueError(f"Missing environment variables: {missing_vars}")
```

### 4. **Clientes de Servicios Externos**

```python
from whatsapp_webhook.external_services import (
    send_to_agent,
    send_whatsapp_message,
    download_whatsapp_media
)

# Enviar mensaje al agente
response = await send_to_agent(
    app_name="AA",
    user_id="1234567890",
    session_id="session_123",
    message="Hola"
)

# Enviar mensaje a WhatsApp
result = await send_whatsapp_message(
    to="1234567890",
    message={"type": "text", "text": {"body": "Hola"}},
    whatsapp_api_url=api_url,
    token=token
)
```

## 📋 Migración

### Para mantener compatibilidad:

El archivo `utils.py` original sigue funcionando pero está marcado como **DEPRECATED**. Muestra un warning y re-exporta las funciones desde los nuevos módulos.

### Para migrar código existente:

```python
# ❌ Antiguo (deprecated)
from whatsapp_webhook.utils import idtoken_from_metadata_server, get_logger

# ✅ Nuevo
from whatsapp_webhook.auth.google_auth import idtoken_from_metadata_server
from whatsapp_webhook.utils.logging import get_logger
```

## 🎯 Beneficios

1. **Modularidad**: Cada módulo tiene una responsabilidad específica
2. **Testabilidad**: Más fácil crear tests unitarios para funciones específicas
3. **Mantenibilidad**: Código más organizado y fácil de mantener
4. **Reutilización**: Funciones específicas pueden ser reutilizadas independientemente
5. **Logging Estructurado**: Mejor observabilidad y debugging
6. **Type Safety**: Mejor soporte para type hints y validación

## 🚀 Próximos Pasos

1. Migrar gradualmente las importaciones al nuevo sistema
2. Implementar el sistema de registry con decoradores (según REFACTOR_PLAN.md)
3. Crear tests unitarios para cada módulo
4. Remover el archivo `utils.py` deprecated cuando se complete la migración
