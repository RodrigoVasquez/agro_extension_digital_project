# Configuración de Logging para Webhook Application

## Descripción

La aplicación webhook ahora soporta configuración dinámica del nivel de logging a través de variables de entorno, permitiendo diferentes niveles de verbosidad según el ambiente de deployment.

## Configuración

### Variable de Entorno

- **`LOG_LEVEL`**: Define el nivel de logging de la aplicación
  - **Valores válidos**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - **Valor por defecto**: `INFO`

### Configuración por Ambiente

#### Development (`dev`)
- **Nivel configurado**: `DEBUG`
- **Propósito**: Logging detallado para desarrollo y debugging
- **Impacto**: Mayor volumen de logs, ideal para troubleshooting

#### Production (`prd`)
- **Nivel configurado**: `INFO`
- **Propósito**: Logging balanceado para monitoreo en producción
- **Impacto**: Logs informativos sin exceso de detalle

## Implementación Técnica

### 1. Código de la Aplicación (`main.py`)

```python
def configure_logging():
    """Configure logging level based on environment variable."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        log_level = "INFO"
        print(f"Warning: Invalid LOG_LEVEL provided. Using default: INFO")
    
    # Convert string to logging level
    numeric_level = getattr(logging, log_level)
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logging.info(f"Logging configured with level: {log_level}")
```

### 2. Variable de Terraform (`variables.tf`)

```hcl
variable "log_level" {
    description = "Nivel de logging para la aplicación webhook (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    type        = string
    default     = "INFO"
}
```

### 3. Configuración Cloud Run (`main.tf`)

```hcl
env {
  name  = "LOG_LEVEL"
  value = var.log_level
}
```

### 4. Configuración Terragrunt

#### Development (`cicd/dev/terragrunt.hcl`)
```hcl
log_level = "DEBUG"  # Development environment uses DEBUG level for detailed logging
```

#### Production (`cicd/prd/terragrunt.hcl`)
```hcl
log_level = "INFO"  # Production environment uses INFO level for performance and log volume control
```

## Beneficios

1. **Flexibilidad**: Diferentes niveles de logging por ambiente
2. **Performance**: Menos logs en producción mejora el rendimiento
3. **Debugging**: Logs detallados en desarrollo facilitan el troubleshooting
4. **Monitoreo**: Nivel apropiado de información en producción
5. **Configuración dinámica**: Sin necesidad de cambiar código para ajustar logging

## Niveles de Logging Disponibles

- **DEBUG**: Información detallada para debugging (dev)
- **INFO**: Información general sobre el funcionamiento (prd por defecto)
- **WARNING**: Situaciones potencialmente problemáticas
- **ERROR**: Errores que no detienen la aplicación
- **CRITICAL**: Errores críticos que pueden afectar el funcionamiento

## Deployment

Al hacer deploy con Terragrunt, la variable `log_level` se pasará automáticamente como variable de entorno al contenedor de Cloud Run, configurando el nivel de logging apropiado para cada ambiente.

```bash
# Development deployment
terragrunt apply  # Usa LOG_LEVEL=DEBUG

# Production deployment  
cd ../prd && terragrunt apply  # Usa LOG_LEVEL=INFO
```
