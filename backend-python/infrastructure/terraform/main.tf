terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Backend configuration for state storage
  # Uncomment and configure when ready to use remote state
  # backend "gcs" {
  #   bucket = "liftlog-terraform-state"
  #   prefix = "python-backend"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (staging or production)"
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro" # Use db-custom-2-7680 for production
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "liftlog-python-backend"
}

variable "container_image" {
  description = "Container image URL"
  type        = string
}

# Outputs
output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.backend.status[0].url
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.user_data.connection_name
}

output "database_ip" {
  description = "Cloud SQL instance IP"
  value       = google_sql_database_instance.user_data.public_ip_address
}
