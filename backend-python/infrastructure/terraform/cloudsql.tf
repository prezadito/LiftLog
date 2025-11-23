# Cloud SQL PostgreSQL Instance for User Data
resource "google_sql_database_instance" "user_data" {
  name             = "liftlog-user-data-${var.environment}"
  database_version = "POSTGRES_17"
  region           = var.region

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10 # GB, auto-increases if needed
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00" # 3 AM UTC
      point_in_time_recovery_enabled = var.environment == "production"
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled    = true
      private_network = null # Set to VPC network ID for private IP
      require_ssl     = true

      authorized_networks {
        name  = "allow-all-for-cloud-run"
        value = "0.0.0.0/0" # Cloud Run requires public IP or Cloud SQL Proxy
      }
    }

    maintenance_window {
      day          = 7 # Sunday
      hour         = 4 # 4 AM UTC
      update_track = "stable"
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }

  deletion_protection = var.environment == "production"
}

# User Data Database
resource "google_sql_database" "user_data" {
  name     = "liftlog_user_data"
  instance = google_sql_database_instance.user_data.name
}

# Rate Limit Database (same instance, different database)
resource "google_sql_database" "rate_limit" {
  name     = "liftlog_rate_limit"
  instance = google_sql_database_instance.user_data.name
}

# Database User
resource "google_sql_user" "backend_user" {
  name     = "liftlog_backend"
  instance = google_sql_database_instance.user_data.name
  password = var.db_password # Set via environment variable or secret manager
}

variable "db_password" {
  description = "Database password for backend user"
  type        = string
  sensitive   = true
}
