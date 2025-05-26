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

resource "google_project_iam_member" "agent_aa_sa_role_discovery" {   
    project = var.project_id
    role    = "roles/discoveryengine.user"
    member  = "serviceAccount:${google_service_account.agent_aa_app.email}"
}

resource "google_project_iam_member" "agent_aa_connection_user" {   
    project = var.project_id
    role    = "roles/connectors.user"
    member  = "serviceAccount:${google_service_account.agent_aa_app.email}"
}

resource "google_project_iam_member" "agent_aa_integration_invoker" {   
    project = var.project_id
    role    = "roles/integrations.integrationInvoker"
    member  = "serviceAccount:${google_service_account.agent_aa_app.email}"
}

resource "google_cloud_run_v2_service" "cloud_run_name_agent_aa" {
  name     = var.cloud_run_name_agent_aa
  location = var.region
  project  = var.project_id

  template {
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
        name  = "DATASTORE_AA_ID"
        value = var.datastore_aa_id
      }
      env {
        name  = "DATASTORE_PP_ID"
        value = var.datastore_pp_id
      }
      env {
        name  = "DATASTORE_GUIDES_ID"
        value = var.datastore_guides_id
      }
      env {
        name  = "DATASTORE_FAQ_ID"
        value = var.datastore_faq_id
      }
      env {
        name  = "DATASTORE_CHILEPRUNES_CL_ID"
        value = var.datastore_chileprunes_cl_id
        }
      env {
        name  = "BIGQUERY_INTEGRATION_APPLICATION_CONNECTOR_ID"
        value = var.bigquery_integration_application_connector_id
        }
    }

    service_account = google_service_account.agent_aa_app.email
  }

  ingress = "INGRESS_TRAFFIC_ALL"

}

resource "google_cloud_run_v2_service_iam_binding" "noauth" {
    name        = google_cloud_run_v2_service.cloud_run_name_agent_aa.name
    project     = var.project_id
    location    = var.region
    role        = "roles/run.invoker"
    members     = ["allUsers"]
}

terraform {
  backend "gcs" {}
}