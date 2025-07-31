# Diagrama de Secuencia - Procesamiento de Mensajes WhatsApp

## 📋 Flujo Principal de Mensajes

```mermaid
sequenceDiagram
    participant WA as WhatsApp Business API
    participant WH as Webhook Endpoint
    participant VP as Validador de Payload
    participant PM as Procesador de Mensajes
    participant SM as Manejador de Sesiones
    participant AG as Servicio de Agente
    participant AU as Autenticador Google
    participant WS as WhatsApp Send API

    Note over WA, WS: Flujo Completo de Procesamiento de Mensajes

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
        VP-->>WH: return (termina)
    end

    %% 3. Procesamiento por tipo de mensaje
    loop Para cada mensaje extraído
        alt Mensaje de texto
            VP->>PM: _process_single_text_message()
            
            %% ACK inmediato
            PM->>WS: _send_whatsapp_acknowledgment("✓")
            WS-->>PM: success/failure
            
            %% Procesamiento con agente
            PM->>SM: create_session()
            SM-->>PM: session_created
            
            PM->>PM: message.get_message_content()
            PM->>AG: send_message()
            
            %% Autenticación con el agente
            AG->>AU: idtoken_from_metadata_server()
            AU-->>AG: id_token
            
            %% Comunicación con agente
            AG->>AG: create_agent_request() (Pydantic)
            AG->>AG: POST /run (con Bearer token)
            AG->>AG: parse_agent_response()
            AG-->>PM: agent_response_text
            
            %% Envío de respuesta final
            PM->>WS: _send_whatsapp_acknowledgment(agent_response)
            WS-->>PM: success/failure
            
        else Mensaje no-texto
            VP->>PM: _process_non_text_message()
            
            %% ACK inmediato
            PM->>WS: _send_whatsapp_acknowledgment("✓")
            WS-->>PM: success/failure
            
            %% Mensaje informativo
            PM->>WS: _send_whatsapp_acknowledgment("Solo puedo procesar mensajes de texto...")
            WS-->>PM: success/failure
        end
        
        %% Manejo de errores
        alt Error en procesamiento
            PM->>WS: _send_whatsapp_acknowledgment("Error procesando mensaje...")
            WS-->>PM: success/failure
        end
    end

    VP-->>WH: procesamiento_completo
    WH-->>WA: HTTP 200 OK
```

## 🔧 Detalles Técnicos del Flujo

### 1. **Entrada del Webhook**
```
WhatsApp → receive_message_aa/pp() → process_incoming_webhook_payload()
```

### 2. **Validación y Parsing**
```
_validate_webhook_config() → parse_webhook_payload() → get_all_messages()
```

### 3. **Procesamiento de Mensajes de Texto**
```mermaid
sequenceDiagram
    participant PM as Procesador
    participant WS as WhatsApp API
    participant AG as Agente

    PM->>WS: ACK "✓" (inmediato)
    PM->>AG: send_message(texto)
    AG-->>PM: respuesta_agente
    PM->>WS: respuesta_agente (final)
```

### 4. **Procesamiento de Mensajes No-Texto**
```mermaid
sequenceDiagram
    participant PM as Procesador
    participant WS as WhatsApp API

    PM->>WS: ACK "✓" (inmediato)
    PM->>WS: "Solo puedo procesar mensajes de texto..." (informativo)
```

## 📊 Componentes y Responsabilidades

### **Validador de Payload** (`_validate_webhook_config`)
- ✅ Valida variables de entorno
- ✅ Retorna configuración o falla

### **Parser de Webhook** (`parse_webhook_payload`)
- ✅ Usa modelos Pydantic para validación
- ✅ Extrae todos los tipos de mensajes
- ❌ **Sin backward compatibility** - Si falla, termina

### **Procesador de Mensajes de Texto** (`_process_single_text_message`)
1. **ACK inmediato:** `✓` 
2. **Crear sesión:** `create_session()`
3. **Extraer contenido:** `message.get_message_content()`
4. **Comunicar con agente:** `send_message()`
5. **Respuesta final:** Respuesta del agente

### **Procesador de Mensajes No-Texto** (`_process_non_text_message`)
1. **ACK inmediato:** `✓`
2. **Mensaje informativo:** Explicación sobre solo texto

### **Comunicación con Agente** (`send_message`)
1. **Mapeo de app:** `get_agent_app_name()`
2. **Autenticación:** Google ID token
3. **Request Pydantic:** `create_agent_request()`
4. **POST al agente:** `/run` endpoint
5. **Parse respuesta:** `parse_agent_response()`

## 🚀 Características del Sistema Actual

### ✅ **Optimizaciones**
- **ACK inmediato** previene reenvíos de WhatsApp
- **Sin mensajes "procesando"** redundantes
- **Solo modelos Pydantic** - código limpio
- **Manejo robusto de errores** en cada paso

### ❌ **Sin Backward Compatibility**
- No hay procesamiento legacy
- No hay fallbacks de parsing
- No hay funciones de compatibilidad
- Falla limpiamente si no puede parsear

### 🔄 **Flujo Simplificado**
```
Webhook → Validar → Parsear → Procesar → ACK + Respuesta
```

## 📈 **Ventajas del Diseño Actual**

1. **Performance:** ACK inmediato evita timeouts
2. **Simplicidad:** Una sola ruta de procesamiento
3. **Robustez:** Manejo de errores en cada paso
4. **Escalabilidad:** Modelos Pydantic bien definidos
5. **Mantenibilidad:** Código limpio sin legacy
