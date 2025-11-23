# LiftLog Python Backend Infrastructure

This directory contains Infrastructure as Code (IaC) and deployment scripts for the LiftLog Python/FastAPI backend.

## 📁 Directory Structure

```
infrastructure/
├── terraform/              # Terraform configuration files
│   ├── main.tf            # Main Terraform config and variables
│   ├── cloudsql.tf        # Cloud SQL PostgreSQL setup
│   ├── cloudrun.tf        # Cloud Run service configuration
│   ├── secrets.tf         # Secret Manager configuration
│   └── terraform.tfvars.example  # Example variables file
├── scripts/               # Deployment automation scripts
│   ├── deploy.sh         # Deployment script
│   └── rollback.sh       # Rollback script
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Install required tools:**
   - [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)
   - [Terraform](https://www.terraform.io/downloads) (>= 1.0)

2. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Set your GCP project:**
   ```bash
   export GCP_PROJECT_ID="your-gcp-project-id"
   gcloud config set project $GCP_PROJECT_ID
   ```

4. **Enable required APIs:**
   ```bash
   gcloud services enable \
     run.googleapis.com \
     sqladmin.googleapis.com \
     secretmanager.googleapis.com \
     compute.googleapis.com
   ```

### Initial Setup

1. **Configure Terraform variables:**
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   vim terraform.tfvars
   ```

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

3. **Create staging workspace:**
   ```bash
   terraform workspace new staging
   terraform workspace select staging
   ```

4. **Plan the deployment:**
   ```bash
   terraform plan -var="environment=staging"
   ```

5. **Apply the configuration:**
   ```bash
   terraform apply -var="environment=staging"
   ```

### Using Deployment Scripts

The deployment scripts automate the Terraform workflow:

#### Deploy to Staging

```bash
cd scripts
./deploy.sh staging latest
```

#### Deploy to Production

```bash
./deploy.sh production v1.0.0
```

#### Rollback to Previous Revision

```bash
./rollback.sh staging
```

#### Rollback to Specific Revision

```bash
./rollback.sh staging liftlog-python-backend-staging-00005-abc
```

## 🏗️ Infrastructure Components

### Cloud SQL PostgreSQL

- **Instance**: Managed PostgreSQL 17 database
- **Databases**:
  - `liftlog_user_data` - User data and events
  - `liftlog_rate_limit` - Rate limiting consumption tracking
- **Backups**: Daily automated backups with 7-day retention
- **High Availability**: REGIONAL for production, ZONAL for staging
- **Security**: SSL/TLS required, authorized networks configured

### Cloud Run

- **Service**: Containerized FastAPI application
- **Autoscaling**:
  - Staging: 0-10 instances
  - Production: 1-50 instances
- **Resources**:
  - Staging: 1 CPU, 2GB RAM
  - Production: 2 CPU, 4GB RAM
- **Concurrency**: 80 requests per instance
- **Timeout**: 60 seconds

### Secret Manager

Stores sensitive configuration:
- `openai-api-key` - OpenAI API key for AI features
- `web-auth-api-key` - Web authentication signing key
- `google-play-email` - Google Play service account email
- `google-play-key` - Google Play service account key (base64)

## 🔐 Managing Secrets

### Create Secrets via gcloud

```bash
# OpenAI API Key
echo -n "sk-your-openai-key" | gcloud secrets create openai-api-key-staging --data-file=-

# Web Auth API Key
echo -n "your-web-auth-key" | gcloud secrets create web-auth-api-key-staging --data-file=-

# Google Play credentials
echo -n "service-account@project.iam.gserviceaccount.com" | gcloud secrets create google-play-email-staging --data-file=-
cat service-account-key.json | base64 | gcloud secrets create google-play-key-staging --data-file=-
```

### Update Secrets

```bash
echo -n "new-secret-value" | gcloud secrets versions add openai-api-key-staging --data-file=-
```

### Grant Access to Service Account

```bash
gcloud secrets add-iam-policy-binding openai-api-key-staging \
  --member="serviceAccount:liftlog-backend-staging@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## 🗄️ Database Management

### Connect to Cloud SQL

```bash
# Install Cloud SQL Proxy
gcloud components install cloud-sql-proxy

# Connect to database
gcloud sql connect liftlog-user-data-staging --user=liftlog_backend
```

### Run Migrations

```bash
# Option 1: Via local connection with Cloud SQL Proxy
cd backend-python
export DATABASE_URL="postgresql+asyncpg://liftlog_backend:PASSWORD@localhost:5432/liftlog_user_data"
uv run alembic upgrade head

# Option 2: Via Cloud Run Jobs (recommended for production)
# TODO: Set up Cloud Run Job for migrations
```

### Backup and Restore

```bash
# List backups
gcloud sql backups list --instance=liftlog-user-data-staging

# Restore from backup
gcloud sql backups restore BACKUP_ID --backup-instance=liftlog-user-data-staging
```

## 📊 Monitoring and Logs

### View Cloud Run Logs

```bash
# Tail logs
gcloud run logs tail liftlog-python-backend-staging --region=us-central1

# View logs in Cloud Console
gcloud run services describe liftlog-python-backend-staging --region=us-central1 --format="value(status.url)"
# Navigate to Cloud Console > Cloud Run > Service > Logs
```

### View Cloud SQL Metrics

```bash
# Cloud Console > SQL > Instance > Monitoring
```

### Set up Alerts

See Cloud Console > Monitoring > Alerting for configuring alerts on:
- Error rates
- Response latency
- Database connections
- Memory usage

## 🧪 Testing the Deployment

### Health Check

```bash
SERVICE_URL=$(gcloud run services describe liftlog-python-backend-staging \
  --region=us-central1 \
  --format="value(status.url)")

curl $SERVICE_URL/health
# Expected: {"status":"ok"}
```

### Test API Endpoints

```bash
# Create a test user
curl -X POST "$SERVICE_URL/v2/user/create" \
  -H "Content-Type: application/json" \
  -d '{}'

# Get user
curl "$SERVICE_URL/v2/user/USER_ID" \
  -H "Authorization: PASSWORD"
```

## 🔄 CI/CD Integration

The GitHub Actions workflows automatically deploy on:

1. **Push to main** → Build and push Docker image
2. **Manual trigger** → Deploy to staging or production

See `.github/workflows/python-backend-*.yml` for workflow definitions.

## 📝 Environment Variables

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host/db` |
| `RATE_LIMIT_DATABASE_URL` | Rate limit DB connection | Same as DATABASE_URL |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `WEB_AUTH_API_KEY` | Web auth signing key | Random secure string |
| `GOOGLE_PLAY_SERVICE_ACCOUNT_EMAIL` | Google Play email | `service@project.iam.gserviceaccount.com` |
| `GOOGLE_PLAY_SERVICE_ACCOUNT_KEY_BASE64` | Google Play key | Base64-encoded JSON key |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TEST_MODE` | Enable test mode (bypass rate limiting) | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CLEANUP_INTERVAL_MINUTES` | Cleanup job interval | `60` |

## 🚨 Troubleshooting

### Service won't start

1. Check logs: `gcloud run logs tail SERVICE_NAME --region=us-central1`
2. Verify environment variables are set correctly
3. Ensure secrets are accessible by service account
4. Check database connectivity

### Database connection errors

1. Verify Cloud SQL instance is running
2. Check database credentials
3. Ensure service account has `roles/cloudsql.client` role
4. Verify database exists and migrations have run

### Secret access denied

1. Check service account permissions:
   ```bash
   gcloud secrets get-iam-policy SECRET_NAME
   ```
2. Grant access if missing:
   ```bash
   gcloud secrets add-iam-policy-binding SECRET_NAME \
     --member="serviceAccount:SERVICE_ACCOUNT@PROJECT.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

## 📚 Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

## 🆘 Support

For issues or questions:
1. Check the [main README](../../README.md)
2. Review logs in Cloud Console
3. Open an issue on GitHub
