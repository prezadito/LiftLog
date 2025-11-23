# Secret Manager Secrets
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    service     = "liftlog-backend"
  }
}

resource "google_secret_manager_secret" "web_auth_api_key" {
  secret_id = "web-auth-api-key-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    service     = "liftlog-backend"
  }
}

resource "google_secret_manager_secret" "google_play_email" {
  secret_id = "google-play-email-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    service     = "liftlog-backend"
  }
}

resource "google_secret_manager_secret" "google_play_key" {
  secret_id = "google-play-key-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    service     = "liftlog-backend"
  }
}

# Note: Secret versions need to be created manually or via separate terraform apply
# Example: gcloud secrets versions add openai-api-key-production --data-file=path/to/secret

# Variables for secret values (optional - can be set externally)
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "web_auth_api_key" {
  description = "Web auth API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_play_service_account_email" {
  description = "Google Play service account email"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_play_service_account_key" {
  description = "Google Play service account key (base64)"
  type        = string
  sensitive   = true
  default     = ""
}

# Create initial secret versions if values are provided
resource "google_secret_manager_secret_version" "openai_api_key" {
  count = var.openai_api_key != "" ? 1 : 0

  secret      = google_secret_manager_secret.openai_api_key.id
  secret_data = var.openai_api_key
}

resource "google_secret_manager_secret_version" "web_auth_api_key" {
  count = var.web_auth_api_key != "" ? 1 : 0

  secret      = google_secret_manager_secret.web_auth_api_key.id
  secret_data = var.web_auth_api_key
}

resource "google_secret_manager_secret_version" "google_play_email" {
  count = var.google_play_service_account_email != "" ? 1 : 0

  secret      = google_secret_manager_secret.google_play_email.id
  secret_data = var.google_play_service_account_email
}

resource "google_secret_manager_secret_version" "google_play_key" {
  count = var.google_play_service_account_key != "" ? 1 : 0

  secret      = google_secret_manager_secret.google_play_key.id
  secret_data = var.google_play_service_account_key
}
