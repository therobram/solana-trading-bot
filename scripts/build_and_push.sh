### 📁 scripts/build_and_push.sh
#!/bin/bash

# Script para construir y subir imágenes Docker a Google Artifact Registry

# Variables
PROJECT_ID="tu-proyecto-gcp"
REGION="us-central1"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/trading-bot"

# Verificar que gcloud esté configurado
if ! gcloud auth print-access-token &>/dev/null; then
  echo "Error: No estás autenticado en gcloud. Ejecuta 'gcloud auth login' primero."
  exit 1
fi

# Verificar que el repositorio exista o crearlo
if ! gcloud artifacts repositories describe trading-bot --location=${REGION} &>/dev/null; then
  echo "Creando repositorio de artefactos 'trading-bot'..."
  gcloud artifacts repositories create trading-bot \
    --repository-format=docker \
    --location=${REGION} \
    --description="Repositorio para el bot de trading de Solana"
fi

# Configurar docker para usar gcloud como credencial helper
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Construir y subir cada servicio
services=("rpc_service" "token_scanner" "trading_engine" "api_gateway")

for service in "${services[@]}"; do
  echo "Construyendo imagen para ${service}..."
  docker build -t ${REGISTRY}/${service}:latest ./${service}
  
  echo "Subiendo imagen ${service} a Artifact Registry..."
  docker push ${REGISTRY}/${service}:latest
done

echo "Todas las imágenes han sido construidas y subidas exitosamente."