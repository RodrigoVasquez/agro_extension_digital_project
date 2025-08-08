variable "project_id" {
  description = "ID del proyecto de Google Cloud"
  type        = string
}

variable "cloud_run_name_agent_aa" {
  description = "Nombre del servicio de Cloud Run"
  type        = string
}

variable "cloud_run_name_agent_pp" {
  description = "Nombre del servicio de Cloud Run"
  type        = string
}

variable "service_account_id_agent_aa" {
  description = "ID de la cuenta de servicio del agente"
  type        = string
}

variable "service_account_id_agent_pp" {
  description = "ID de la cuenta de servicio del agente"
  type        = string
}

variable "service_account_display_name_agent_aa" {
  description = "Nombre para mostrar de la cuenta de servicio del agente"
  type        = string
}

variable "service_account_display_name_agent_pp" {
  description = "Nombre para mostrar de la cuenta de servicio del agente"
  type        = string
}

variable "region" {
  description = "Ubicación de los servicios"
  type        = string
}

variable "gar_image_location_agent_aa" {
    description = "Ubicación de la imagen del servicio de Cloud Run"
    type        = string
}

variable "google_genai_use_vertexai" {
    description = "Flag to indicate if Vertex AI should be used"
    type        = string
    default     = "TRUE"
}

variable "google_cloud_project" {
    description = "Google Cloud project ID"
    type        = string
}

variable "google_cloud_location" {
    description = "Google Cloud location"
    type        = string
    default     = "us-central1"
}

variable "service_name" {
    description = "Name of the service"
    type        = string
    default     = "adecuacion_agroindustrial"
}

variable "datastore_aa_id" {
    description = "Datastore ID for AA"
    type        = string
}

variable "datastore_pp_id" {
    description = "Datastore ID for PP"
    type        = string
}

variable "datastore_guides_id" {
    description = "Datastore ID for guides"
    type        = string
}

variable "datastore_faq_id" {
    description = "Datastore ID for FAQ"
    type        = string
}

variable "datastore_chileprunes_cl_id" {
    description = "Datastore ID for Chileprunes CL"
    type        = string
}

variable "cloud_run_name_webhook" {
  description = "Nombre del servicio de Cloud Run para el webhook"
  type        = string
}

variable "gar_image_location_webhook" {
    description = "Ubicación de la imagen del servicio de Cloud Run"
    type        = string
}

variable "estandar_aa_facebook_app" {
    description = "URL del servicio de Facebook para AA"
    type        = string
}

variable "estandar_pp_facebook_app" {
    description = "URL del servicio de Facebook para PP"
    type        = string
}

variable "verify_token" {
    description = "Token de verificación"
    type        = string
}

variable "service_account_webhook_app" {
    description = "Cuenta de servicio para el webhook"
    type        = string
}

variable "service_account_display_name_webhook_app" {
    description = "Nombre para mostrar de la cuenta de servicio del webhook"
    type        = string
}

variable "estandar_aa_app_name" {
    description = "URL del servicio de Facebook para AA"
    type        = string
}

variable "estandar_pp_app_name" {
    description = "URL del servicio de Facebook para AA"
    type        = string
}

variable "wsp_token" {
    description = "Token de WhatsApp"
    type        = string
}

variable "whatsapp_base_url" {
    description = "Base URL for WhatsApp Graph API"
    type        = string
    default     = "https://graph.facebook.com/v22.0"
}

variable "cpu_limit_agent" {
    description = "CPU limit for agent services"
    type        = string
    default     = "2"
}

variable "memory_limit_agent" {
    description = "Memory limit for agent services"
    type        = string
    default     = "4Gi"
}

variable "cpu_limit_webhook" {
    description = "CPU limit for webhook service"
    type        = string
    default     = "1"
}

variable "memory_limit_webhook" {
    description = "Memory limit for webhook service"
    type        = string
    default     = "2Gi"
}

variable "min_instances_agent_aa" {
    description = "Minimum instances for AA agent"
    type        = number
    default     = 1
}

variable "min_instances_webhook" {
    description = "Minimum instances for webhook"
    type        = number
    default     = 1
}

variable "max_concurrency" {
    description = "Maximum concurrent requests per instance"
    type        = number
    default     = 80
}

variable "log_level" {
    description = "Nivel de logging para la aplicación webhook (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    type        = string
    default     = "INFO"
}

variable "bigquery_dataset" {
    description = "BigQuery dataset name for the agents"
    type        = string
}