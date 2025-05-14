GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=agro-extension-digital-npe
GOOGLE_CLOUD_LOCATION=us-central1
SERVICE_NAME="adecuacion-agroindustrial"
APP_NAME="adecuacion-agroindustrial"
AGENT_PATH=agent

gcloud run deploy agent-aa \
--source . \
--region $GOOGLE_CLOUD_LOCATION \
--project $GOOGLE_CLOUD_PROJECT \
--allow-unauthenticated \
--set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,GOOGLE_GENAI_USE_VERTEXAI=$GOOGLE_GENAI_USE_VERTEXAI"