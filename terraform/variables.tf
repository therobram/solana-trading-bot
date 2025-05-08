### 📁 terraform/variables.tf
variable "project_id" {
  description = "ID del proyecto GCP"
  type        = string
}

variable "region" {
  description = "Región de GCP"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Zona de GCP"
  type        = string
  default     = "us-central1-a"
}

variable "artifact_registry_location" {
  description = "Ubicación del Artifact Registry"
  type        = string
  default     = "us-central1"
}

variable "mongodb_host" {
  description = "Host de MongoDB Atlas"
  type        = string
}

variable "mongodb_user" {
  description = "Usuario de MongoDB"
  type        = string
}

variable "mongodb_password" {
  description = "Contraseña de MongoDB"
  type        = string
  sensitive   = true
}

variable "wallet_private_key_json" {
  description = "Clave privada de la wallet Solana en formato JSON array"
  type        = string
  sensitive   = true
}

variable "rpc_solana" {
  description = "URL del RPC de Solana"
  type        = string
  default     = "https://api.mainnet-beta.solana.com"
}

# Agrega más variables para todos tus RPCs