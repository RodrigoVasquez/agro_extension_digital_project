# Diagrama de Secuencia - Procesamiento de Mensajes WhatsApp

## 📋 Flujo Principal de Mensajes

```mermaid
sequenceDiagram
    participant WA as WhatsApp Business API
    participant WH as Webhook Endpoint
    participant VP as Validador de Payload
    participant BG as Procesador Background
    participant SM as Manejador de Sesiones
    participant AG as Servicio de Agente
    participant AU as Autenticador Google
    participant WS as WhatsApp Send API

    Note over WA, WS: Flujo con ACK Inmediato + Procesamiento Background

    %% 1. Recepción del webhook
    WA->>WH: POST /webhook (payload)
    WH->>WH: receive_message_aa() / receive_message_pp()
    WH->>VP: process_incoming_webhook_payload()

    %% 2. Validación inicial
    VP->>VP: _validate_webhook_config()
    alt Config válida
        VP->>VP: parse_webhook_payload() (Pydantic)
        VP->>VP: webhook_payload.get_all_messages()
    else Config inválida
        VP-->>WH: return False (HTTP 500)
    end

    %% 3. ACK inmediato a Facebook
    VP->>BG: asyncio.create_task(_process_messages_in_background())
    Note over VP, BG: Inicia procesamiento en background SIN esperar
    VP-->>WH: return True (ACK INMEDIATO)
    WH-->>WA: HTTP 200 OK [ACK FACEBOOK]
    Note over WH, WA: ACK crítico enviado en <1 segundo

    %% 4. Procesamiento en background (paralelo)
    par Procesamiento Background
        loop Para cada mensaje en background
            alt Mensaje de texto
                BG->>SM: create_session()
                SM-->>BG: session_created
                
                BG->>BG: message.get_message_content()
                BG->>AG: send_message()
                
                %% Autenticación con el agente
                AG->>AU: idtoken_from_metadata_server()
                AU-->>AG: id_token
                
                %% Comunicación con agente
                AG->>AG: create_agent_request() (Pydantic)
                AG->>AG: POST /run (con Bearer token)
                AG->>AG: parse_agent_response()
                AG-->>BG: agent_response_text
                
                %% Envío de respuesta al usuario
                BG->>WS: _send_whatsapp_acknowledgment(agent_response)
                WS-->>BG: success/failure
                Note over BG, WS: Respuesta del agente enviada al usuario
                
            else Mensaje no-texto
                %% Mensaje informativo directo
                BG->>WS: _send_whatsapp_acknowledgment("Solo puedo procesar mensajes de texto...")
                WS-->>BG: success/failure
                Note over BG, WS: Mensaje informativo enviado al usuario
            end
            
            %% Manejo de errores en background
            alt Error en procesamiento background
                BG->>WS: _send_whatsapp_acknowledgment("Error procesando mensaje...")
                WS-->>BG: success/failure
                Note over BG, WS: Mensaje de error enviado al usuario
            end
        end
    end
```

## 🔧 Detalles Técnicos del Flujo

### 1. **Entrada del Webhook**
```
WhatsApp → receive_message_aa/pp() → process_incoming_webhook_payload() → ACK INMEDIATO (HTTP 200) + Background Processing
```

### 2. **ACK Inmediato a Facebook**
```
_validate_webhook_config() → parse_webhook_payload() → asyncio.create_task() → return True → HTTP 200
```

### 3. **Procesamiento Background Asíncrono**
```mermaid
sequenceDiagram
    participant VP as Validador
    participant BG as Background Task
    participant AG as Agente
    participant WS as WhatsApp

    VP->>BG: create_task() [NO ESPERA]
    VP-->>VP: return True (ACK Facebook)
    
    par Background Processing
        BG->>AG: send_message(texto)
        AG-->>BG: respuesta_agente
        BG->>WS: respuesta_agente [VISIBLE AL USUARIO]
    end
```

## 📊 Componentes y Responsabilidades

### **Validador de Payload** (`process_incoming_webhook_payload`)
- ✅ Valida variables de entorno
- ✅ Parsea webhook con Pydantic
- ✅ **ACK inmediato** a Facebook (return True)
- ✅ Inicia procesamiento background con `asyncio.create_task()`

### **Procesador Background** (`_process_messages_in_background`)
- ✅ Procesa mensajes de forma asíncrona
- ✅ No bloquea el ACK a Facebook
- ✅ Maneja errores independientemente

### **Procesador de Mensajes de Texto** (`_process_single_text_message`)
1. **Crear sesión:** `create_session()`
2. **Extraer contenido:** `message.get_message_content()`
3. **Comunicar con agente:** `send_message()`
4. **Respuesta directa:** Respuesta del agente (ejecutado en background)

### **Procesador de Mensajes No-Texto** (`_process_non_text_message`)
1. **Mensaje informativo directo:** Explicación sobre solo texto (ejecutado en background)

### **Comunicación con Agente** (`send_message`)
1. **Mapeo de app:** `get_agent_app_name()`
2. **Autenticación:** Google ID token
3. **Request Pydantic:** `create_agent_request()`
4. **POST al agente:** `/run` endpoint
5. **Parse respuesta:** `parse_agent_response()`

## 🚀 Características del Sistema Actual

### ✅ **Optimizaciones**
- **ACK inmediato a Facebook** (<1 segundo) previene reenvíos de WhatsApp
- **Procesamiento background** sin bloquear respuesta HTTP
- **Sin timeouts** - Facebook recibe ACK inmediatamente
- **Procesamiento paralelo** con asyncio.create_task()
- **Solo modelos Pydantic** - código limpio
- **Manejo robusto de errores** con ACK garantizado
- **UX óptima:** Solo mensajes útiles al usuario

### ❌ **Sin Backward Compatibility**
- No hay procesamiento legacy
- No hay fallbacks de parsing
- No hay funciones de compatibilidad
- Falla limpiamente si no puede parsear

### 🔄 **Flujo Optimizado**
```
Webhook → Validar → Parsear → ACK INMEDIATO Facebook (HTTP 200) + Background Task → Procesar → Respuesta Usuario
```

## 📈 **Ventajas del Diseño Actual**

1. **Performance crítico:** ACK inmediato a Facebook (<1s) evita timeouts y reenvíos
2. **Escalabilidad:** Procesamiento background no bloquea nuevos webhooks
3. **Robustez:** Manejo de errores independiente en background
4. **Disponibilidad:** Sistema siempre responde rápido a Facebook
5. **Arquitectura moderna:** asyncio.create_task() para concurrencia
6. **UX óptima:** Solo mensajes útiles y relevantes al usuario
