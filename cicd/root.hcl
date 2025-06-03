remote_state {
  backend = "gcs"

  config = {
    bucket  = local.terragrunt_state_bucket # These locals must be defined in child terragrunt.hcl
    prefix  = "${path_relative_to_include()}/terraform.tfstate"
    project = local.terragrunt_state_project # These locals must be defined in child terragrंट.hcl
    location = "us-central1"            # Can also be made a local if it needs to vary
  }
}

inputs = {
  region = "us-central1"
  zone   = "us-central1-a"
}