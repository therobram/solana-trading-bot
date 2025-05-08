### 📁 scripts/deploy.sh
#!/bin/bash

# Script para desplegar infraestructura en GCP usando Terraform

# Variables
TERRAFORM_DIR="./terraform"
TFVARS_FILE="${TERRAFORM_DIR}/terraform.tfvars"

# Verificar que terraform esté instalado
if ! command -v terraform &>/dev/null; then
  echo "Error: Terraform no está instalado. Instálalo desde https://www.terraform.io/downloads.html"
  exit 1
fi

# Verificar que el archivo terraform.tfvars exista
if [ ! -f "${TFVARS_FILE}" ]; then
  echo "Error: No se encontró el archivo ${TFVARS_FILE}"
  echo "Crea el archivo terraform.tfvars basado en terraform.tfvars.example"
  exit 1
fi

# Inicializar Terraform
echo "Inicializando Terraform..."
cd ${TERRAFORM_DIR}
terraform init

# Verificar plan de Terraform
echo "Generando plan de Terraform..."
terraform plan -out=tfplan

# Confirmar despliegue
read -p "¿Deseas proceder con el despliegue? (s/n): " confirm
if [ "$confirm" != "s" ]; then
  echo "Despliegue cancelado."
  exit 0
fi

# Aplicar cambios
echo "Desplegando infraestructura..."
terraform apply tfplan

# Mostrar outputs
echo "Despliegue completado. Información de endpoints:"
terraform output