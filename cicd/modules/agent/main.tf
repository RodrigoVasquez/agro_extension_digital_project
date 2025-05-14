resource "google_service_account" "agent_aa_app" {
    account_id   = var.service_account_id_agent_aa
    display_name = var.service_account_display_name_agent_aa
    project = var.project_id
}

resource "google_project_iam_member" "agent_aa_sa_role" {   
    project = var.project_id
    role    = "roles/aiplatform.user"
    member  = "serviceAccount:${google_service_account.agent_aa_app.email}"
}

resource "google_cloud_run_service" "cloud_run_name_agent_aa" {
    name     = var.cloud_run_name_agent_aa
    location = var.region
    project  = var.project_id
    template {
        spec {
            service_account_name = google_service_account.agent_aa_app.email
            containers {
                image = var.gar_image_location_agent_aa
                env {
                    name  = "GOOGLE_GENAI_USE_VERTEXAI"
                    value = var.google_genai_use_vertexai
                }
                env {
                    name  = "GOOGLE_CLOUD_PROJECT"
                    value = var.google_cloud_project
                }
                env {
                    name  = "GOOGLE_CLOUD_LOCATION"
                    value = var.google_cloud_location
                }
                env {
                    name  = "SERVICE_NAME"
                    value = var.service_name
                }
                env {
                    name  = "DATASTORE_ID_AA"
                    value = var.datastore_id_aa
                }
                env {
                    name  = "DATASTORE_ID_PP"
                    value = var.datastore_id_pp
                }
                env {
                    name  = "DATASTORE_GUIDES_ID"
                    value = var.datastore_guides_id
                }
                env {
                    name  = "DATASTORE_FAQ_ID"
                    value = var.datastore_faq_id
                }
                
            }
        }
    }
    metadata {
        annotations = {
            "run.googleapis.com/ingress" = "all"
        }
  }
    
}

terraform {
  backend "gcs" {}
}