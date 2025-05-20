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
    default     = "agro-extension-digital-npe"
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

variable "datastore_aa_structured_id" {
    description = "Datastore ID for AA structured data"
    type        = string
}
