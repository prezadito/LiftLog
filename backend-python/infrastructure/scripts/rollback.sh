#!/bin/bash
set -e

# LiftLog Python Backend Rollback Script
# This script rolls back the Cloud Run service to a previous revision

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
    echo "Usage: $0 <environment> [revision]"
    echo "Example: $0 staging liftlog-python-backend-staging-00005-abc"
    echo "If revision is not provided, will rollback to previous revision"
    exit 1
fi

ENVIRONMENT=$1
REVISION=$2

# Validate environment
if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    print_error "Environment must be 'staging' or 'production'"
    exit 1
fi

# Service name
SERVICE_NAME="liftlog-python-backend"
if [ "$ENVIRONMENT" == "staging" ]; then
    SERVICE_NAME="liftlog-python-backend-staging"
fi

REGION="us-central1"

print_warning "⚠️  ROLLBACK INITIATED for $ENVIRONMENT environment"

# Check if gcloud is installed
command -v gcloud >/dev/null 2>&1 || { print_error "gcloud is not installed. Install it from https://cloud.google.com/sdk"; exit 1; }

# List current revisions
print_info "Current revisions for $SERVICE_NAME:"
gcloud run revisions list \
    --service="$SERVICE_NAME" \
    --region="$REGION" \
    --format="table(name, status, trafficPercent, creationTimestamp)" \
    --limit=10

# If revision not provided, get the previous revision
if [ -z "$REVISION" ]; then
    print_info "No revision specified, finding previous revision..."

    # Get current serving revision
    CURRENT_REVISION=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format="value(status.traffic[0].revisionName)")

    print_info "Current revision: $CURRENT_REVISION"

    # Get previous revision (second in the list)
    REVISION=$(gcloud run revisions list \
        --service="$SERVICE_NAME" \
        --region="$REGION" \
        --format="value(name)" \
        --limit=2 | tail -n 1)

    if [ -z "$REVISION" ] || [ "$REVISION" == "$CURRENT_REVISION" ]; then
        print_error "Could not find a previous revision to rollback to"
        exit 1
    fi

    print_info "Will rollback to: $REVISION"
fi

# Ask for confirmation (skip in CI)
if [ -z "$CI" ]; then
    read -p "Rollback to revision $REVISION? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        print_warning "Rollback cancelled"
        exit 0
    fi
fi

# Perform rollback
print_info "Rolling back to revision: $REVISION"
gcloud run services update-traffic "$SERVICE_NAME" \
    --region="$REGION" \
    --to-revisions="$REVISION=100"

# Wait a moment for the change to propagate
sleep 5

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --format="value(status.url)")

# Run smoke test
print_info "Running smoke test..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health")

if [ "$HTTP_STATUS" -eq 200 ]; then
    print_info "✅ Health check passed"
else
    print_error "❌ Health check failed with status $HTTP_STATUS"
    print_warning "Consider rolling back further or investigating the issue"
    exit 1
fi

# Print rollback summary
echo ""
print_info "=========================================="
print_info "Rollback Summary"
print_info "=========================================="
echo "Environment: $ENVIRONMENT"
echo "Service: $SERVICE_NAME"
echo "Revision: $REVISION"
echo "Service URL: $SERVICE_URL"
echo "Health Check: ✅ Passed"
print_info "=========================================="
echo ""

print_info "Rollback complete! ✅"
print_warning "Monitor the service closely for any issues"
print_warning "Check logs: gcloud run logs tail $SERVICE_NAME --region=$REGION"
