### 📁 terraform/main.tf
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# VPC Network
resource "google_compute_network" "vpc_network" {
  name                    = "trading-bot-vpc"
  auto_create_subnetworks = "true"
}

# Cloud Run Microservices
resource "google_cloud_run_service" "rpc_service" {
  name     = "rpc-service"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/trading-bot/rpc-service:latest"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
        
        env {
          name  = "MONGO_URI"
          value = "mongodb+srv://${var.mongodb_user}:${var.mongodb_password}@${var.mongodb_host}/trading_bot?retryWrites=true&w=majority"
        }
        
        # Aquí agregarás todas las variables RPC_*
        # Ejemplo:
        env {
          name  = "RPC_SOLANA"
          value = var.rpc_solana
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service" "token_scanner" {
  name     = "token-scanner"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/trading-bot/token-scanner:latest"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
        
        env {
          name  = "MONGO_URI"
          value = "mongodb+srv://${var.mongodb_user}:${var.mongodb_password}@${var.mongodb_host}/trading_bot?retryWrites=true&w=majority"
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service" "trading_engine" {
  name     = "trading-engine"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/trading-bot/trading-engine:latest"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "1Gi"
          }
        }
        
        env {
          name  = "MONGO_URI"
          value = "mongodb+srv://${var.mongodb_user}:${var.mongodb_password}@${var.mongodb_host}/trading_bot?retryWrites=true&w=majority"
        }
        
        env {
          name  = "PRIVATE_KEY_JSON"
          value = var.wallet_private_key_json
        }
        
        env {
          name  = "RPC_SOLANA"
          value = var.rpc_solana
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service" "api_gateway" {
  name     = "api-gateway"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/trading-bot/api-gateway:latest"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
        
        env {
          name  = "RPC_SERVICE_URL"
          value = google_cloud_run_service.rpc_service.status[0].url
        }
        
        env {
          name  = "TOKEN_SCANNER_URL"
          value = google_cloud_run_service.token_scanner.status[0].url
        }
        
        env {
          name  = "TRADING_ENGINE_URL"
          value = google_cloud_run_service.trading_engine.status[0].url
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# IAM Policy para acceso público al API Gateway
resource "google_cloud_run_service_iam_member" "api_gateway_public" {
  service  = google_cloud_run_service.api_gateway.name
  location = google_cloud_run_service.api_gateway.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Scheduler para ciclos de trading
resource "google_cloud_scheduler_job" "trading_cycle_job" {
  name             = "trading-cycle-job"
  description      = "Ejecuta ciclo de trading cada 5 minutos"
  schedule         = "*/5 * * * *"
  time_zone        = "America/Santiago"
  attempt_deadline = "180s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.api_gateway.status[0].url}/cycle"
    
    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }
  
  depends_on = [google_cloud_run_service.api_gateway]
}

# Service Account para Cloud Scheduler
resource "google_service_account" "scheduler_sa" {
  account_id   = "scheduler-sa"
  display_name = "Service Account para Cloud Scheduler"
}

resource "google_cloud_run_service_iam_member" "scheduler_invoker" {
  service  = google_cloud_run_service.api_gateway.name
  location = google_cloud_run_service.api_gateway.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

# Cloud SQL para MongoDB (alternativa a MongoDB Atlas)
# Comentado porque preferimos usar MongoDB Atlas
/*
resource "google_sql_database_instance" "mongodb_instance" {
  name             = "trading-bot-mongodb"
  database_version = "MONGODB_4_4"
  region           = var.region

  settings {
    tier = "db-f1-micro"
    
    backup_configuration {
      enabled = true
      start_time = "02:00"
    }
  }
}

resource "google_sql_user" "mongodb_user" {
  name     = var.mongodb_user
  instance = google_sql_database_instance.mongodb_instance.name
  password = var.mongodb_password
}
*/

# Variables de salida
output "api_gateway_url" {
  value = google_cloud_run_service.api_gateway.status[0].url
}