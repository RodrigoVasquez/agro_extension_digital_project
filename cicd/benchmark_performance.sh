#!/bin/bash

# Script de benchmark para medir el rendimiento de los servicios optimizados
# Utiliza Artillery.js para pruebas de carga y mide métricas específicas de Cloud Run

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
    log_error "Uso: $0 <webhook_url> <environment>"
    log_info "Ejemplo: $0 https://agent-webhook-dev-123abc.a.run.app dev"
    exit 1
fi

WEBHOOK_URL=$1
ENVIRONMENT=$2
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="./benchmark_results_${ENVIRONMENT}_${TIMESTAMP}"

log_info "Iniciando benchmark para $WEBHOOK_URL ($ENVIRONMENT)"

# Crear directorio de resultados
mkdir -p "$RESULTS_DIR"

# Verificar dependencias
check_dependencies() {
    log_info "Verificando dependencias..."
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js no está instalado"
        exit 1
    fi
    
    if ! command -v npx &> /dev/null; then
        log_error "npx no está disponible"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        log_error "curl no está instalado"
        exit 1
    fi
    
    log_success "Todas las dependencias están disponibles"
}

# Instalar Artillery si no está disponible
install_artillery() {
    if ! command -v artillery &> /dev/null; then
        log_info "Instalando Artillery.js..."
        npm install -g artillery@latest
        log_success "Artillery instalado correctamente"
    else
        log_info "Artillery ya está instalado: $(artillery version)"
    fi
}

# Crear configuración de Artillery
create_artillery_config() {
    log_info "Creando configuración de pruebas..."
    
    # Configuración básica para health check
    cat > "$RESULTS_DIR/health_check.yml" << EOF
config:
  target: '${WEBHOOK_URL}'
  phases:
    - duration: 60
      arrivalRate: 1
      name: "Health check warm-up"
    - duration: 300
      arrivalRate: 5
      name: "Sustained health check load"
  plugins:
    metrics-by-endpoint:
      useOnlyRequestNames: true

scenarios:
  - name: "Health Check Test"
    weight: 100
    requests:
      - get:
          url: "/health"
          name: "health_endpoint"
EOF

    # Configuración para cold start testing
    cat > "$RESULTS_DIR/cold_start.yml" << EOF
config:
  target: '${WEBHOOK_URL}'
  phases:
    - duration: 10
      arrivalRate: 1
      name: "Cold start test"
  plugins:
    metrics-by-endpoint:
      useOnlyRequestNames: true

scenarios:
  - name: "Cold Start Test"
    weight: 100
    requests:
      - get:
          url: "/health"
          name: "cold_start_health"
          beforeRequest: "waitFor5Seconds"

functions:
  waitFor5Seconds: |
    function(requestParams, context, ee, next) {
      setTimeout(function() {
        return next();
      }, 5000);
    }
EOF

    # Configuración para prueba de estrés del webhook
    cat > "$RESULTS_DIR/webhook_stress.yml" << EOF
config:
  target: '${WEBHOOK_URL}'
  phases:
    - duration: 60
      arrivalRate: 1
      name: "Warm-up"
    - duration: 180
      arrivalRate: 10
      name: "Sustained load"
    - duration: 60
      arrivalRate: 20
      name: "Peak load"
  plugins:
    metrics-by-endpoint:
      useOnlyRequestNames: true

scenarios:
  - name: "WhatsApp Webhook Simulation"
    weight: 80
    requests:
      - post:
          url: "/webhook"
          name: "webhook_post"
          headers:
            Content-Type: "application/json"
          json:
            object: "whatsapp_business_account"
            entry: [
              {
                id: "123456789",
                changes: [
                  {
                    value: {
                      messaging_product: "whatsapp",
                      metadata: {
                        display_phone_number: "1234567890",
                        phone_number_id: "987654321"
                      },
                      contacts: [
                        {
                          profile: {
                            name: "Test User"
                          },
                          wa_id: "1234567890"
                        }
                      ],
                      messages: [
                        {
                          from: "1234567890",
                          id: "wamid.test123",
                          timestamp: "1625097600",
                          text: {
                            body: "Test message for performance testing"
                          },
                          type: "text"
                        }
                      ]
                    },
                    field: "messages"
                  }
                ]
              }
            ]
  - name: "Health Check"
    weight: 20
    requests:
      - get:
          url: "/health"
          name: "health_check"
EOF

    log_success "Configuraciones de Artillery creadas"
}

# Ejecutar prueba de cold start
run_cold_start_test() {
    log_info "Ejecutando prueba de cold start..."
    
    # Esperar a que todas las instancias se enfríen
    log_info "Esperando 2 minutos para cold start completo..."
    sleep 120
    
    # Medir tiempo de primer request
    local start_time=$(date +%s%N)
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "${WEBHOOK_URL}/health")
    local end_time=$(date +%s%N)
    local cold_start_ms=$(( (end_time - start_time) / 1000000 ))
    
    echo "Cold Start Time: ${cold_start_ms}ms" > "$RESULTS_DIR/cold_start_manual.txt"
    echo "Response Code: $response_code" >> "$RESULTS_DIR/cold_start_manual.txt"
    
    log_success "Cold start manual: ${cold_start_ms}ms (Response: $response_code)"
    
    # Ejecutar prueba de Artillery para cold starts
    artillery run "$RESULTS_DIR/cold_start.yml" --output "$RESULTS_DIR/cold_start_artillery.json" > "$RESULTS_DIR/cold_start_artillery.log" 2>&1
    
    log_success "Prueba de cold start completada"
}

# Ejecutar prueba de health check
run_health_check_test() {
    log_info "Ejecutando prueba de health check..."
    
    artillery run "$RESULTS_DIR/health_check.yml" --output "$RESULTS_DIR/health_check.json" > "$RESULTS_DIR/health_check.log" 2>&1
    
    if [ $? -eq 0 ]; then
        log_success "Prueba de health check completada"
    else
        log_error "Falló la prueba de health check"
    fi
}

# Ejecutar prueba de estrés del webhook
run_webhook_stress_test() {
    log_info "Ejecutando prueba de estrés del webhook..."
    
    artillery run "$RESULTS_DIR/webhook_stress.yml" --output "$RESULTS_DIR/webhook_stress.json" > "$RESULTS_DIR/webhook_stress.log" 2>&1
    
    if [ $? -eq 0 ]; then
        log_success "Prueba de estrés del webhook completada"
    else
        log_warning "Prueba de estrés del webhook completada con warnings"
    fi
}

# Generar reportes
generate_reports() {
    log_info "Generando reportes..."
    
    # Generar reportes HTML si los archivos JSON existen
    for test in health_check webhook_stress cold_start_artillery; do
        if [ -f "$RESULTS_DIR/${test}.json" ]; then
            artillery report "$RESULTS_DIR/${test}.json" --output "$RESULTS_DIR/${test}_report.html" 2>/dev/null || log_warning "No se pudo generar reporte HTML para $test"
        fi
    done
    
    # Crear resumen
    cat > "$RESULTS_DIR/summary.md" << EOF
# Benchmark Results - $ENVIRONMENT

**Timestamp:** $(date)
**Target URL:** $WEBHOOK_URL
**Environment:** $ENVIRONMENT

## Cold Start Performance

$(cat "$RESULTS_DIR/cold_start_manual.txt" 2>/dev/null || echo "No data available")

## Test Results

### Health Check Test
- Log file: health_check.log
- JSON report: health_check.json
- HTML report: health_check_report.html

### Webhook Stress Test
- Log file: webhook_stress.log
- JSON report: webhook_stress.json
- HTML report: webhook_stress_report.html

### Cold Start Artillery Test
- Log file: cold_start_artillery.log
- JSON report: cold_start_artillery.json
- HTML report: cold_start_artillery_report.html

## Analysis Recommendations

1. **Cold Start Time**: Should be < 5 seconds for optimal performance
2. **Response Time**: P95 should be < 2 seconds under normal load
3. **Error Rate**: Should be < 1% for production workloads
4. **Throughput**: Verify it meets expected traffic patterns

## Next Steps

1. Review individual HTML reports for detailed metrics
2. Compare against previous benchmarks
3. Analyze Cloud Run logs for any errors during tests
4. Consider infrastructure optimizations if performance targets not met

EOF

    log_success "Reportes generados en: $RESULTS_DIR"
}

# Función principal
main() {
    check_dependencies
    install_artillery
    create_artillery_config
    
    log_info "Iniciando secuencia de pruebas..."
    
    # Ejecutar pruebas en secuencia
    run_cold_start_test
    sleep 30  # Pausa entre pruebas
    
    run_health_check_test
    sleep 30  # Pausa entre pruebas
    
    run_webhook_stress_test
    
    # Generar reportes finales
    generate_reports
    
    log_success "Benchmark completado exitosamente!"
    log_info "Resultados disponibles en: $RESULTS_DIR"
    log_info "Para ver reportes HTML, abre los archivos *_report.html en tu navegador"
    
    # Mostrar resumen rápido
    echo ""
    log_info "=== RESUMEN RÁPIDO ==="
    if [ -f "$RESULTS_DIR/cold_start_manual.txt" ]; then
        cat "$RESULTS_DIR/cold_start_manual.txt"
    fi
    
    echo ""
    log_info "Archivos generados:"
    ls -la "$RESULTS_DIR"
}

# Ejecutar función principal
main
