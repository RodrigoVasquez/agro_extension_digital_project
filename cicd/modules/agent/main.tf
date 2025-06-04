resource "google_service_account" "agent_aa_app" {
    account_id   = var.service_account_id_agent_aa
    display_name = var.service_account_display_name_agent_aa
    project = var.project_id
}

resource "google_service_account" "webhook_app_sa" {
    account_id   = var.service_account_webhook_app
    display_name = var.service_account_display_name_webhook_app
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

resource "google_project_iam_member" "agent_aa_connection_invoker" {   
    project = var.project_id
    role    = "roles/connectors.invoker"
    member  = "serviceAccount:${google_service_account.agent_aa_app.email}"
}

resource "google_project_iam_member" "agent_aa_connection_viewer" {   
    project = var.project_id
    role    = "roles/connectors.viewer"
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

resource "google_cloud_run_v2_service" "cloud_run_name_webhook" {
  name     = var.cloud_run_name_webhook
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = var.gar_image_location_webhook

      env {
        name  = "APP_URL"
        value = google_cloud_run_v2_service.cloud_run_name_agent_aa.uri # Changed from var.app_url
      }
      env {
        name  = "ESTANDAR_AA_FACEBOOK_APP"
        value = var.estandar_aa_facebook_app
      }
      env {
        name  = "ESTANDAR_PP_FACEBOOK_APP"
        value = var.estandar_pp_facebook_app
      }
      env {
        name  = "VERIFY_TOKEN"
        value = var.verify_token
      }
      env {
        name  = "ESTANDAR_AA_APP_NAME"
        value = var.estandar_aa_app_name
      }
      env {
        name  = "ESTANDAR_PP_APP_NAME"
        value = var.estandar_pp_app_name
      }

      env {
        name  = "WSP_TOKEN"
        value = var.wsp_token
      }
    }

    service_account = google_service_account.webhook_app_sa.email
  }

  ingress = "INGRESS_TRAFFIC_ALL"
  depends_on = [google_cloud_run_v2_service.cloud_run_name_agent_aa]
}


resource "google_cloud_run_v2_service_iam_binding" "noauth_webhook" {
    name        = google_cloud_run_v2_service.cloud_run_name_webhook.name
    project     = var.project_id
    location    = var.region
    role        = "roles/run.invoker"
    members     = ["allUsers"]
}

resource "google_cloud_run_v2_service_iam_member" "webhook_invokes_agent_aa" {
  name     = google_cloud_run_v2_service.cloud_run_name_agent_aa.name
  project  = var.project_id
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.webhook_app_sa.email}"
}

terraform {
  backend "gcs" {}
}

output "agent_aa_service_url" {
  description = "The URL of the agent-aa Cloud Run service."
  value       = google_cloud_run_v2_service.cloud_run_name_agent_aa.uri
}