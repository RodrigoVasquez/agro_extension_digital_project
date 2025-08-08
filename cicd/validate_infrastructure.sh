#!/bin/bash

# Script para validar las optimizaciones de infraestructura Cloud Run
# Este script verifica que las configuraciones de rendimiento estén aplicadas correctamente

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validar parámetros
if [ "$#" -ne 2 ]; then
    log_error "Uso: $0 <project_id> <environment>"
    log_info "Ejemplo: $0 agro-extension-digital-prd prd"
    exit 1
fi

PROJECT_ID=$1
ENVIRONMENT=$2
REGION="us-central1"

log_info "Validando optimizaciones de infraestructura para $PROJECT_ID ($ENVIRONMENT)"

# Función para verificar configuración de Cloud Run
check_cloud_run_service() {
    local service_name=$1
    local expected_cpu=$2
    local expected_memory=$3
    local expected_min_instances=$4
    
    log_info "Verificando servicio: $service_name"
    
    # Obtener configuración actual
    local config=$(gcloud run services describe $service_name \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="json" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        log_error "No se pudo obtener información del servicio $service_name"
        return 1
    fi
    
    # Verificar CPU
    local actual_cpu=$(echo "$config" | jq -r '.spec.template.spec.containers[0].resources.limits.cpu')
    if [ "$actual_cpu" = "$expected_cpu" ]; then
        log_success "CPU configurada correctamente: $actual_cpu"
    else
        log_warning "CPU no coincide. Esperado: $expected_cpu, Actual: $actual_cpu"
    fi
    
    # Verificar memoria
    local actual_memory=$(echo "$config" | jq -r '.spec.template.spec.containers[0].resources.limits.memory')
    if [ "$actual_memory" = "$expected_memory" ]; then
        log_success "Memoria configurada correctamente: $actual_memory"
    else
        log_warning "Memoria no coincide. Esperado: $expected_memory, Actual: $actual_memory"
    fi
    
    # Verificar instancias mínimas
    local actual_min_instances=$(echo "$config" | jq -r '.spec.template.metadata.annotations."autoscaling.knative.dev/minScale" // "0"')
    if [ "$actual_min_instances" = "$expected_min_instances" ]; then
        log_success "Instancias mínimas configuradas correctamente: $actual_min_instances"
    else
        log_warning "Instancias mínimas no coinciden. Esperado: $expected_min_instances, Actual: $actual_min_instances"
    fi
    
    # Verificar startup CPU boost
    local startup_boost=$(echo "$config" | jq -r '.spec.template.spec.containers[0].resources.startupCpuBoost // false')
    if [ "$startup_boost" = "true" ]; then
        log_success "Startup CPU boost habilitado"
    else
        log_warning "Startup CPU boost no está habilitado"
    fi
    
    echo ""
}

# Función para verificar variables de entorno
check_environment_variables() {
    local service_name=$1
    
    log_info "Verificando variables de entorno para: $service_name"
    
    local config=$(gcloud run services describe $service_name \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="json" 2>/dev/null)
    
    # Verificar WHATSAPP_BASE_URL
    local whatsapp_url=$(echo "$config" | jq -r '.spec.template.spec.containers[0].env[] | select(.name=="WHATSAPP_BASE_URL") | .value')
    if [ "$whatsapp_url" = "https://graph.facebook.com/v22.0" ]; then
        log_success "WHATSAPP_BASE_URL configurada correctamente"
    else
        log_warning "WHATSAPP_BASE_URL no configurada o incorrecta: $whatsapp_url"
    fi
    
    # Verificar LOG_LEVEL
    local log_level=$(echo "$config" | jq -r '.spec.template.spec.containers[0].env[] | select(.name=="LOG_LEVEL") | .value')
    local expected_log_level
    if [ "$ENVIRONMENT" = "prd" ]; then
        expected_log_level="INFO"
    else
        expected_log_level="DEBUG"
    fi
    
    if [ "$log_level" = "$expected_log_level" ]; then
        log_success "LOG_LEVEL configurado correctamente: $log_level"
    else
        log_warning "LOG_LEVEL no coincide. Esperado: $expected_log_level, Actual: $log_level"
    fi
    
    echo ""
}

# Configuraciones específicas por entorno
if [ "$ENVIRONMENT" = "prd" ]; then
    # Configuraciones de producción
    WEBHOOK_SERVICE="agent-webhook-prd"
    AGENT_AA_SERVICE="agent-aa-prd"
    
    WEBHOOK_CPU="1"
    WEBHOOK_MEMORY="2Gi"
    WEBHOOK_MIN_INSTANCES="1"
    
    AGENT_CPU="2"
    AGENT_MEMORY="4Gi"
    AGENT_MIN_INSTANCES="1"
else
    # Configuraciones de desarrollo
    WEBHOOK_SERVICE="agent-webhook-dev"
    AGENT_AA_SERVICE="agent-dev"
    
    WEBHOOK_CPU="1"
    WEBHOOK_MEMORY="1Gi"
    WEBHOOK_MIN_INSTANCES="0"
    
    AGENT_CPU="1"
    AGENT_MEMORY="2Gi"
    AGENT_MIN_INSTANCES="0"
fi

# Verificar autenticación
log_info "Verificando autenticación con Google Cloud..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    log_error "No hay cuentas autenticadas. Ejecuta: gcloud auth login"
    exit 1
fi

# Configurar proyecto
gcloud config set project $PROJECT_ID

# Verificar servicios
log_info "Verificando servicios de Cloud Run..."

# Verificar webhook
check_cloud_run_service "$WEBHOOK_SERVICE" "$WEBHOOK_CPU" "$WEBHOOK_MEMORY" "$WEBHOOK_MIN_INSTANCES"
check_environment_variables "$WEBHOOK_SERVICE"

# Verificar agente AA
check_cloud_run_service "$AGENT_AA_SERVICE" "$AGENT_CPU" "$AGENT_MEMORY" "$AGENT_MIN_INSTANCES"
check_environment_variables "$AGENT_AA_SERVICE"

# Verificar métricas de rendimiento
log_info "Verificando métricas de rendimiento recientes..."

# Cold start latency
log_info "Analizando latencia de cold start en los últimos 7 días..."
gcloud logging read "
resource.type=\"cloud_run_revision\" AND
resource.labels.service_name=\"$WEBHOOK_SERVICE\" AND
httpRequest.latency>\"1s\"
" \
--limit=10 \
--project=$PROJECT_ID \
--format="table(timestamp,httpRequest.latency,httpRequest.status)" || log_warning "No se pudieron obtener métricas de latencia"

# Resumen final
log_info "Validación completada para $PROJECT_ID ($ENVIRONMENT)"
log_success "Revisa los warnings anteriores para optimizaciones adicionales"

# Comandos útiles para monitoreo
echo ""
log_info "Comandos útiles para monitoreo continuo:"
echo "# Ver logs en tiempo real:"
echo "gcloud logs tail --project=$PROJECT_ID --filter='resource.type=\"cloud_run_revision\"'"
echo ""
echo "# Verificar métricas de CPU:"
echo "gcloud monitoring metrics list --project=$PROJECT_ID --filter='metric.type:run.googleapis.com/container/cpu'"
echo ""
echo "# Analizar cold starts:"
echo "gcloud logging read 'resource.type=\"cloud_run_revision\" AND textPayload:\"Cold start\"' --project=$PROJECT_ID --limit=50"
