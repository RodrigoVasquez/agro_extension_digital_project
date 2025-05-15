include "root" {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  project_id = "agro-extension-digital-npe"
  environment = "dev"
  location = "us-central1"
  cloud_run_name_agent_aa = "agent-aa-dev"
  cloud_run_name_agent_pp = "agent-pp-dev"
  service_account_id_agent_aa = "agent-aa-sa-dev"
  service_account_display_name_agent_aa = "Agent AA Service Account"
  service_account_id_agent_pp = "agent-pp-sa-dev"
  service_account_display_name_agent_pp = "Agent PP Service Account"
  region = "us-central1"
  gar_image_location_agent_aa = "us-central1-docker.pkg.dev/agro-extension-digital-npe/agents/agent-aa-app:latest"
  gar_image_location_agent_pp = "us-central1-docker.pkg.dev/agro-extension-digital-npe/agents/agent-pp-app:latest"
  google_genai_use_vertexai = "TRUE"
  google_cloud_project = "agro-extension-digital-npe"
  google_cloud_location = "us-central1"
  service_name = "agent-aa-dev"
  datastore_id_aa = "projects/agro-extension-digital-npe/locations/global/collections/default_collection/dataStores/0001-adecuacion-agroindustrial_1745450263959"
  datastore_id_pp = "projects/agro-extension-digital-npe/locations/global/collections/default_collection/dataStores/0001-produccion-primaria_1745450565038"
  datastore_guides_id = "projects/agro-extension-digital-npe/locations/global/collections/default_collection/dataStores/0001-guias_1745450505033"
  datastore_faq_id = "projects/agro-extension-digital-npe/locations/global/collections/default_collection/dataStores/0001-faq_1745450327301"
}

terraform {
  source = "../modules/agent"
}
