remote_state {
  backend = "gcs"

  config = {
    bucket         = "agro-extension-digital-tf-state-bucket" # Nombre del bucket
    prefix         = "${path_relative_to_include()}/terraform.tfstate" # Ruta del estado
    project        = "agro-extension-digital-npe"
    location       = "us-central1"            # Región del bucket
  }
}

inputs = {
  region = "us-central1"
  zone   = "us-central1-a"
}