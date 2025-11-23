#!/bin/bash
set -e

# LiftLog Python Backend Deployment Script
# This script deploys the Python backend to Google Cloud Run

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if environment argument is provided
if [ -z "$1" ]; then
    print_error "Environment argument required (staging or production)"
    echo "Usage: $0 <environment> [image-tag]"
    echo "Example: $0 staging latest"
    exit 1
fi

ENVIRONMENT=$1
IMAGE_TAG=${2:-latest}

# Validate environment
if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    print_error "Environment must be 'staging' or 'production'"
    exit 1
fi

print_info "Deploying to $ENVIRONMENT environment with image tag: $IMAGE_TAG"

# Check if required tools are installed
command -v gcloud >/dev/null 2>&1 || { print_error "gcloud is not installed. Install it from https://cloud.google.com/sdk"; exit 1; }
command -v terraform >/dev/null 2>&1 || { print_error "terraform is not installed. Install it from https://www.terraform.io"; exit 1; }

# Set GCP project (from terraform.tfvars or environment variable)
if [ -z "$GCP_PROJECT_ID" ]; then
    print_warning "GCP_PROJECT_ID not set, reading from terraform.tfvars"
    GCP_PROJECT_ID=$(grep 'project_id' ../terraform/terraform.tfvars | cut -d'"' -f2)
fi

if [ -z "$GCP_PROJECT_ID" ]; then
    print_error "Could not determine GCP project ID"
    exit 1
fi

print_info "Using GCP project: $GCP_PROJECT_ID"
gcloud config set project "$GCP_PROJECT_ID"

# Navigate to terraform directory
cd "$(dirname "$0")/../terraform"

# Initialize Terraform
print_info "Initializing Terraform..."
terraform init

# Select or create workspace for environment
print_info "Selecting Terraform workspace: $ENVIRONMENT"
terraform workspace select "$ENVIRONMENT" 2>/dev/null || terraform workspace new "$ENVIRONMENT"

# Plan the deployment
print_info "Planning Terraform deployment..."
terraform plan \
    -var="environment=$ENVIRONMENT" \
    -var="container_image=ghcr.io/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/python-backend:$IMAGE_TAG" \
    -out=tfplan

# Ask for confirmation (skip in CI)
if [ -z "$CI" ]; then
    read -p "Apply this plan? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        print_warning "Deployment cancelled"
        exit 0
    fi
fi

# Apply the plan
print_info "Applying Terraform configuration..."
terraform apply tfplan

# Get the service URL
SERVICE_URL=$(terraform output -raw service_url)
print_info "Service deployed at: $SERVICE_URL"

# Run database migrations
print_info "Running database migrations..."
print_warning "Manual step: Run migrations using Cloud Run Jobs or connect to the Cloud SQL instance"
print_warning "Example: gcloud sql connect liftlog-user-data-$ENVIRONMENT --user=liftlog_backend"
print_warning "Then run: uv run alembic upgrade head"

# Run smoke test
print_info "Running smoke test..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health")

if [ "$HTTP_STATUS" -eq 200 ]; then
    print_info "✅ Health check passed"
else
    print_error "❌ Health check failed with status $HTTP_STATUS"
    exit 1
fi

# Print deployment summary
echo ""
print_info "=========================================="
print_info "Deployment Summary"
print_info "=========================================="
echo "Environment: $ENVIRONMENT"
echo "Service URL: $SERVICE_URL"
echo "Image: ghcr.io/*/python-backend:$IMAGE_TAG"
echo "Health Check: ✅ Passed"
print_info "=========================================="
echo ""

print_info "Deployment complete! 🚀"
print_warning "Remember to:"
print_warning "1. Run database migrations"
print_warning "2. Verify all endpoints are working"
print_warning "3. Check logs for any errors"
print_warning "4. Update mobile clients to use new endpoint"
