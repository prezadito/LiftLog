# Cloud Run Service
resource "google_cloud_run_service" "backend" {
  name     = "${var.service_name}-${var.environment}"
  location = var.region

  template {
    spec {
      containers {
        image = var.container_image

        # Resource limits
        resources {
          limits = {
            cpu    = var.environment == "production" ? "2000m" : "1000m"
            memory = var.environment == "production" ? "4Gi" : "2Gi"
          }
        }

        # Environment variables
        env {
          name  = "TEST_MODE"
          value = "false"
        }

        env {
          name  = "LOG_LEVEL"
          value = var.environment == "production" ? "WARNING" : "INFO"
        }

        # Database connection string
        env {
          name  = "DATABASE_URL"
          value = "postgresql+asyncpg://${google_sql_user.backend_user.name}:${var.db_password}@/${google_sql_database.user_data.name}?host=/cloudsql/${google_sql_database_instance.user_data.connection_name}"
        }

        env {
          name  = "RATE_LIMIT_DATABASE_URL"
          value = "postgresql+asyncpg://${google_sql_user.backend_user.name}:${var.db_password}@/${google_sql_database.rate_limit.name}?host=/cloudsql/${google_sql_database_instance.user_data.connection_name}"
        }

        # Secrets from Secret Manager
        env {
          name = "OPENAI_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.openai_api_key.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "WEB_AUTH_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.web_auth_api_key.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "GOOGLE_PLAY_SERVICE_ACCOUNT_EMAIL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_play_email.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "GOOGLE_PLAY_SERVICE_ACCOUNT_KEY_BASE64"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_play_key.secret_id
              key  = "latest"
            }
          }
        }

        # Health check
        startup_probe {
          http_get {
            path = "/health"
            port = 8000
          }
          initial_delay_seconds = 0
          timeout_seconds       = 1
          period_seconds        = 3
          failure_threshold     = 10
        }

        liveness_probe {
          http_get {
            path = "/health"
            port = 8000
          }
          initial_delay_seconds = 10
          timeout_seconds       = 1
          period_seconds        = 10
          failure_threshold     = 3
        }
      }

      # Cloud SQL connection
      cloud_sql_instances = [google_sql_database_instance.user_data.connection_name]

      # Autoscaling
      container_concurrency = 80
      timeout_seconds       = 60

      service_account_name = google_service_account.backend.email
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.environment == "production" ? "1" : "0"
        "autoscaling.knative.dev/maxScale" = var.environment == "production" ? "50" : "10"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.user_data.connection_name
        "run.googleapis.com/client-name"        = "terraform"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}

# Service Account for Cloud Run
resource "google_service_account" "backend" {
  account_id   = "liftlog-backend-${var.environment}"
  display_name = "LiftLog Python Backend Service Account (${var.environment})"
}

# IAM binding for Cloud Run (allow public access)
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# IAM binding for Secret Manager access
resource "google_secret_manager_secret_iam_member" "backend_secrets" {
  for_each = toset([
    google_secret_manager_secret.openai_api_key.id,
    google_secret_manager_secret.web_auth_api_key.id,
    google_secret_manager_secret.google_play_email.id,
    google_secret_manager_secret.google_play_key.id,
  ])

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

# IAM binding for Cloud SQL Client
resource "google_project_iam_member" "backend_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend.email}"
}
