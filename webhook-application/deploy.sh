docker build -t southamerica-west1-docker.pkg.dev/agro-extension-digital-npe/agro-extension-app/whatsapp-webhook .
docker push southamerica-west1-docker.pkg.dev/agro-extension-digital-npe/agro-extension-app/whatsapp-webhook
gcloud run deploy whatsapp-webhook \
  --image=southamerica-west1-docker.pkg.dev/agro-extension-digital-npe/agro-extension-app/whatsapp-webhook \
  --region=southamerica-west1 \
  --platform=managed \
  --allow-unauthenticated