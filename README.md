Proyecto agroextension digital

Github action self hosted execution

Execute the Action:

1. gcloud auth login

2. gcloud config set project agro-extension-digital-npe

3. gcloud auth application-default login

4. nohup actions-runner/run.sh &

# GCloud Commands for Creating GCS Terraform State Buckets

This document outlines the gcloud commands to create Google Cloud Storage (GCS) buckets intended for storing Terraform state files. Two buckets will be created, one for a non-production environment (NPE) and one for a production environment (PRD).Key Considerations Before Execution:Global Uniqueness of Bucket Names: GCS bucket names must be globally unique. If the specified names are already in use, the creation commands will fail, and you will need to choose slightly different, unique names (e.g., by adding a unique suffix).Permissions: Ensure the Google Cloud account or service account executing these commands has the necessary IAM permissions (e.g., roles/storage.admin or equivalent) in both target projects to create GCS buckets.gcloud CLI: These commands assume you have the Google Cloud CLI installed and authenticated.Bucket 1: For agro-extension-digital-npe ProjectThis bucket is intended for the non-production environment.Target Bucket Name: agro-extension-digital-npe-tf-state-bucketTarget Project ID: agro-extension-digital-npeTarget Location: us-central1Commands:# OPTIONAL: Set your gcloud config to the NPE project.
# This allows omitting the --project flag in subsequent commands for this section.
# gcloud config set project agro-extension-digital-npe

# 1. Create the GCS bucket for the NPE project
echo "Attempting to create bucket 'agro-extension-digital-npe-tf-state-bucket' in project 'agro-extension-digital-npe'..."
gcloud storage buckets create gs://agro-extension-digital-npe-tf-state-bucket \
  --project=agro-extension-digital-npe \
  --location=us-central1 \
  --uniform-bucket-level-access

# 2. Enable versioning on the NPE bucket
# Versioning is highly recommended for Terraform state to allow recovery of previous states.
echo "Enabling versioning for bucket 'agro-extension-digital-npe-tf-state-bucket'..."
gcloud storage buckets update gs://agro-extension-digital-npe-tf-state-bucket \
  --project=agro-extension-digital-npe \
  --versioning

echo "Bucket 'agro-extension-digital-npe-tf-state-bucket' creation and versioning setup process initiated for project 'agro-extension-digital-npe'."
Bucket 2: For agro-extension-digital-prd ProjectThis bucket is intended for the production environment.Target Bucket Name: agro-extension-digital-prd-tf-state-bucketTarget Project ID: agro-extension-digital-prdTarget Location: us-central1 (kept consistent with the NPE bucket for simplicity)Commands:# OPTIONAL: Set your gcloud config to the PRD project.
# This allows omitting the --project flag in subsequent commands for this section.
# gcloud config set project agro-extension-digital-prd

# 1. Create the GCS bucket for the PRD project
echo "Attempting to create bucket 'agro-extension-digital-prd-tf-state-bucket' in project 'agro-extension-digital-prd'..."
gcloud storage buckets create gs://agro-extension-digital-prd-tf-state-bucket \
  --project=agro-extension-digital-prd \
  --location=us-central1 \
  --uniform-bucket-level-access

# 2. Enable versioning on the PRD bucket
# Versioning is highly recommended for Terraform state.
echo "Enabling versioning for bucket 'agro-extension-digital-prd-tf-state-bucket'..."
gcloud storage buckets update gs://agro-extension-digital-prd-tf-state-bucket \
  --project=agro-extension-digital-prd \
  --versioning

echo "Bucket 'agro-extension-digital-prd-tf-state-bucket' creation and versioning setup process initiated for project 'agro-extension-digital-prd'."
After creating these buckets, you will configure your Terraform backend in your .tf files to point to the respective bucket for each environment.