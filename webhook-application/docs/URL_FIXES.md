# Corrección de URLs de WhatsApp y Facebook API

## Problema Identificado

Las URLs de WhatsApp y Facebook API estaban mal administradas para el manejo de media. El problema principal era que:

1. **URLs mal formadas**: Las variables de entorno contenían URLs completas con `/messages` al final, lo que impedía el correcto funcionamiento para descargar media.
2. **URLs hardcoded**: Existían URLs hardcoded desactualizadas en el código.
3. **Inconsistencia**: Diferentes partes del código esperaban diferentes formatos de URL.

## Cambios Realizados

### 1. Actualización de Configuración Terragrunt

**Archivos modificados:**
- `cicd/dev/terragrunt.hcl`
- `cicd/prd/terragrunt.hcl`

**Cambios:**
```hcl
# ANTES
estandar_aa_facebook_app = "https://graph.facebook.com/v22.0/586486637888050/messages"
estandar_pp_facebook_app = "https://graph.facebook.com/v22.0/586486637888050/messages"

# DESPUÉS
estandar_aa_facebook_app = "https://graph.facebook.com/v22.0/586486637888050"
estandar_pp_facebook_app = "https://graph.facebook.com/v22.0/586486637888050"
```

### 2. Actualización del Cliente de WhatsApp

**Archivo:** `webhook-application/whatsapp_webhook/external_services/whatsapp_client.py`

**Cambios:**
- Modificado `send_whatsapp_message()` para construir URL de mensajes correctamente: `${whatsapp_api_url}/messages`
- Actualizado `download_whatsapp_media()` para usar URL base correctamente
- Mejorado `download_media()` para construir URLs de media correctamente

### 3. Actualización de Manejo de Mensajes

**Archivo:** `webhook-application/whatsapp_webhook/messages.py`

**Cambios:**
- Corregido `_send_whatsapp_acknowledgment()` para construir URL correctamente: `${whatsapp_api_url}/messages`

### 4. Actualización de Configuración de Utilidades

**Archivo:** `webhook-application/whatsapp_webhook/utils/config.py`

**Cambios:**
- Eliminadas URLs hardcoded desactualizadas
- Actualizado `get_whatsapp_api_url()` para usar variables de entorno correctas:
  - `ESTANDAR_AA_FACEBOOK_APP` para aplicación AA
  - `ESTANDAR_PP_FACEBOOK_APP` para aplicación PP
- Corregidas funciones `get_facebook_app_env_var()` y `get_app_name_env_var()`

### 5. Actualización de Variables de Entorno Locales

**Archivo:** `webhook-application/.env`

**Cambios:**
```bash
# ANTES
ESTANDAR_AA_FACEBOOK_APP = "https://graph.facebook.com/v22.0/586486637888050/messages"
ESTANDAR_PP_FACEBOOK_APP = "https://graph.facebook.com/v22.0/586486637888050/messages"

# DESPUÉS
ESTANDAR_AA_FACEBOOK_APP = "https://graph.facebook.com/v22.0/586486637888050"
ESTANDAR_PP_FACEBOOK_APP = "https://graph.facebook.com/v22.0/586486637888050"
```

## Beneficios de los Cambios

1. **URLs Base Correctas**: Las URLs ahora son base y se construyen apropiadamente para cada uso específico:
   - `/messages` para envío de mensajes
   - `/{media_id}` para descarga de media

2. **Consistencia**: Todas las partes del código ahora usan el mismo formato de URL base.

3. **Flexibilidad**: El código puede manejar diferentes tipos de endpoints de la Facebook Graph API correctamente.

4. **Compatibilidad**: Los cambios son backward compatible y mejoran la funcionalidad existente.

## Configuración de Variables de Entorno

Las siguientes variables de entorno deben contener URLs base (sin sufijos como `/messages`):

- `ESTANDAR_AA_FACEBOOK_APP`: URL base para aplicación AA
- `ESTANDAR_PP_FACEBOOK_APP`: URL base para aplicación PP
- `WSP_TOKEN`: Token de WhatsApp para autenticación

## Testing y Validación

Para validar que los cambios funcionan correctamente:

1. **Envío de Mensajes**: Verificar que los mensajes de texto se envían correctamente
2. **Descarga de Media**: Probar la descarga de archivos de audio, imagen y otros media
3. **Transcripción de Audio**: Confirmar que la transcripción de audio funciona end-to-end
4. **Logs**: Revisar logs para asegurar que las URLs se construyen correctamente

## URLs de Referencia

### Desarrollo
- AA: `https://graph.facebook.com/v22.0/586486637888050`
- PP: `https://graph.facebook.com/v22.0/586486637888050`

### Producción
- AA: `https://graph.facebook.com/v22.0/692894087240362`
- PP: `https://graph.facebook.com/v22.0/619189944620159`

Estas URLs base se usan para construir:
- Mensajes: `{base_url}/messages`
- Media: `{base_url}/{media_id}`
