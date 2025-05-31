include "root" {
  path = find_in_parent_folders("root.hcl")
}

locals {
  terragrunt_state_bucket = "agro-extension-digital-prd-tf-state-bucket"
  terragrunt_state_project = "agro-extension-digital-prd"
}

inputs = {
  project_id = "agro-extension-digital-prd" # Verified
  environment = "prd" # Changed from dev
  location = "us-central1"
  cloud_run_name_agent_aa = "agent-aa-prd" # Added -prd
  cloud_run_name_agent_pp = "agent-pp-prd" # Added -prd
  service_account_id_agent_aa = "agent-aa-sa-prd" # Added -prd
  service_account_display_name_agent_aa = "Agent AA Service Account PRD" # Added PRD
  service_account_id_agent_pp = "agent-pp-sa-prd" # Added -prd
  service_account_display_name_agent_pp = "Agent PP Service Account PRD" # Added PRD
  region = "us-central1"
  # GAR image locations can remain the same if :latest is used for PRD, or be different if specific PRD tags are used. Assuming same for now.
  gar_image_location_agent_aa = "us-central1-docker.pkg.dev/agro-extension-digital-npe/agents/agent-aa-app:latest"
  gar_image_location_agent_pp = "us-central1-docker.pkg.dev/agro-extension-digital-npe/agents/agent-pp-app:latest"
  google_genai_use_vertexai = "TRUE"
  google_cloud_project = "agro-extension-digital-prd" # Verified
  google_cloud_location = "us-central1"
  service_name = "agent-prd" # Changed from agent-dev

  # Datastore IDs from dev are preserved as per instruction (these might need real PRD values later)
  datastore_aa_id = "projects/agro-extension-digital-npe/locations/global/collections/default_collection/dataStores/0001-adecuacion-agroindustrial_1745450263959"
  datastore_pp_id = "projects/agro-extension-digital-npe/locations/global/collections/default_collection/dataStores/0001-produccion-primaria_1745450565038"
  datastore_guides_id = "projects/agro-extension-digital-npe/locations/global/collections/default_collection/dataStores/0001-guias_1745450505033"
  datastore_faq_id = "projects/agro-extension-digital-npe/locations/global/collections/default_collection/dataStores/0001-faq_1745450327301"
  datastore_chileprunes_cl_id = "projects/agro-extension-digital-npe/locations/global/collections/default_collection/dataStores/0001-chileprunes-cl_1748096068703"

  bigquery_integration_application_connector_id = "c0001-bq-connector" # This might need a -prd suffix or be a different connector for PRD

  service_account_webhook_app = "agent-webhook-sa-prd" # Added -prd
  service_account_display_name_webhook_app = "Agent Webhook Service Account PRD" # Added PRD

  # Secrets - set to placeholder values for PRD
  estandar_aa_facebook_app = "SET_FOR_PRODUCTION_ESTANDAR_AA_FACEBOOK_APP"
  estandar_pp_facebook_app = "SET_FOR_PRODUCTION_ESTANDAR_PP_FACEBOOK_APP"
  verify_token = "SET_FOR_PRODUCTION_VERIFY_TOKEN"

  # GAR image for webhook - assuming same :latest tag for now
  gar_image_location_webhook = "us-central1-docker.pkg.dev/agro-extension-digital-npe/agents/agent-webhook-app:latest"
  cloud_run_name_webhook = "agent-webhook-prd" # Added -prd

  estandar_aa_app_name = "agent_aa_app_prd" # Added _prd
  estandar_pp_app_name = "agent_pp_app_prd" # Added _prd

  wsp_token = "SET_FOR_PRODUCTION_WSP_TOKEN"
}

terraform {
  source = "../modules/agent"
}
