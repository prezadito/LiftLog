# LiftLog Python Backend Deployment Runbook

This runbook provides step-by-step procedures for deploying, monitoring, and troubleshooting the LiftLog Python backend.

## 📋 Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Initial Deployment](#initial-deployment)
- [Routine Deployment](#routine-deployment)
- [Rollback Procedures](#rollback-procedures)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Incident Response](#incident-response)
- [Maintenance Procedures](#maintenance-procedures)

---

## 🔍 Pre-Deployment Checklist

Before deploying to any environment, ensure:

### Code Quality
- [ ] All tests passing (`uv run pytest`)
- [ ] Code formatted (`uv run ruff format .`)
- [ ] Linting passing (`uv run ruff check .`)
- [ ] Type checking passing (`uv run mypy app`)
- [ ] No security vulnerabilities (`uv run bandit -r app`)

### Infrastructure
- [ ] GCP project configured and accessible
- [ ] Database instances running
- [ ] Secrets configured in Secret Manager
- [ ] Service account permissions verified
- [ ] Load balancer configured (production only)

### Documentation
- [ ] CHANGELOG.md updated
- [ ] MIGRATION_ROADMAP.md updated if applicable
- [ ] API documentation reviewed

### Communication
- [ ] Team notified of deployment window
- [ ] Stakeholders informed if production deployment
- [ ] Rollback plan reviewed and understood

---

## 🚀 Initial Deployment

### Step 1: Prepare GCP Environment

```bash
# Set project
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com \
  cloudbuild.googleapis.com
```

### Step 2: Create Secrets

```bash
# Create OpenAI API key secret
echo -n "sk-your-openai-key" | \
  gcloud secrets create openai-api-key-staging --data-file=-

# Create Web Auth API key
openssl rand -hex 32 | \
  gcloud secrets create web-auth-api-key-staging --data-file=-

# Create Google Play credentials
echo -n "service-account@project.iam.gserviceaccount.com" | \
  gcloud secrets create google-play-email-staging --data-file=-

cat service-account-key.json | base64 | \
  gcloud secrets create google-play-key-staging --data-file=-
```

### Step 3: Deploy Infrastructure with Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Create staging workspace
terraform workspace new staging
terraform workspace select staging

# Configure variables
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars  # Edit with your values

# Plan deployment
terraform plan -var="environment=staging" -out=tfplan

# Review plan carefully!
# Ensure no unexpected deletions or changes

# Apply deployment
terraform apply tfplan

# Save outputs
terraform output > ../outputs.txt
```

### Step 4: Run Database Migrations

```bash
# Get Cloud SQL connection name
INSTANCE_CONNECTION_NAME=$(terraform output -raw database_connection_name)

# Option 1: Using Cloud SQL Proxy
cloud-sql-proxy $INSTANCE_CONNECTION_NAME &
PROXY_PID=$!

export DATABASE_URL="postgresql+asyncpg://liftlog_backend:PASSWORD@localhost:5432/liftlog_user_data"
cd ../../
uv run alembic upgrade head

kill $PROXY_PID

# Option 2: Using Cloud SQL Admin API (requires gcloud sql connect)
# See infrastructure/README.md for details
```

### Step 5: Verify Deployment

```bash
# Get service URL
SERVICE_URL=$(terraform output -raw service_url)

# Test health endpoint
curl $SERVICE_URL/health
# Expected: {"status":"ok"}

# Test metrics endpoint
curl $SERVICE_URL/metrics/summary

# Test creating a user
curl -X POST "$SERVICE_URL/v2/user/create" \
  -H "Content-Type: application/json" \
  -d '{}'

# Response should include user_id and password
```

### Step 6: Configure Monitoring

```bash
# Set up Cloud Monitoring alerts
# See "Monitoring and Alerting" section below

# Configure log-based metrics
gcloud logging metrics create error_rate \
  --description="5xx error rate" \
  --log-filter='resource.type="cloud_run_revision" severity=ERROR'

# Create alert policy
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 1%" \
  --condition-threshold-value=0.01 \
  --condition-threshold-duration=300s
```

---

## 🔄 Routine Deployment

For regular deployments after initial setup:

### Quick Deployment (Using Scripts)

```bash
# Navigate to scripts directory
cd infrastructure/scripts

# Deploy to staging
./deploy.sh staging latest

# Deploy to production (requires specific version tag)
./deploy.sh production v1.2.3
```

### Manual Deployment (GitHub Actions)

1. **Push code to main branch:**
   ```bash
   git checkout main
   git pull
   git merge develop
   git push
   ```

2. **Wait for CI/CD pipeline:**
   - GitHub Actions will automatically build Docker image
   - Image will be pushed to GitHub Container Registry

3. **Deploy via GitHub Actions:**
   - Go to GitHub Actions
   - Select "Python Backend Deploy" workflow
   - Click "Run workflow"
   - Select environment (staging/production)
   - Enter image tag (e.g., `v1.2.3` or `latest`)
   - Click "Run workflow"

4. **Monitor deployment:**
   - Watch workflow logs
   - Check Cloud Run console for new revision
   - Verify health check passes

### Post-Deployment Verification

```bash
# 1. Check health endpoint
SERVICE_URL=$(gcloud run services describe liftlog-python-backend-staging \
  --region=us-central1 --format='value(status.url)')
curl $SERVICE_URL/health

# 2. Check metrics
curl $SERVICE_URL/metrics/summary

# 3. Test key endpoints
# User creation
curl -X POST "$SERVICE_URL/v2/user/create" -H "Content-Type: application/json" -d '{}'

# 4. Check logs for errors
gcloud run logs tail liftlog-python-backend-staging \
  --region=us-central1 \
  --limit=50

# 5. Monitor error rates for 15 minutes
# Check Cloud Monitoring dashboard
```

---

## ⏮️ Rollback Procedures

### Automatic Rollback (Using Script)

```bash
cd infrastructure/scripts

# Rollback to previous revision
./rollback.sh staging

# Rollback to specific revision
./rollback.sh staging liftlog-python-backend-staging-00005-abc
```

### Manual Rollback

```bash
# 1. List recent revisions
gcloud run revisions list \
  --service=liftlog-python-backend-staging \
  --region=us-central1 \
  --limit=10

# 2. Identify target revision
# Look for the last known good revision

# 3. Update traffic to target revision
gcloud run services update-traffic liftlog-python-backend-staging \
  --region=us-central1 \
  --to-revisions=liftlog-python-backend-staging-00005-abc=100

# 4. Verify rollback
curl $SERVICE_URL/health

# 5. Monitor logs
gcloud run logs tail liftlog-python-backend-staging --region=us-central1
```

### Rollback Decision Tree

```
Issue Detected
    ↓
Is it critical? (5xx errors > 5%, service down)
    ↓ YES → Rollback immediately
    ↓ NO
    ↓
Can it be fixed quickly? (< 15 minutes)
    ↓ YES → Attempt fix, monitor closely
    ↓ NO → Rollback to last known good
```

---

## 📊 Monitoring and Alerting

### Key Metrics to Monitor

| Metric | Normal Range | Alert Threshold | Action |
|--------|-------------|-----------------|--------|
| **Error Rate** | < 0.1% | > 1% | Investigate logs |
| **Response Time (p95)** | < 200ms | > 500ms | Check database queries |
| **Response Time (p99)** | < 500ms | > 1000ms | Investigate slow endpoints |
| **Database Connections** | < 50 | > 80 | Scale database |
| **Memory Usage** | < 70% | > 85% | Scale Cloud Run instances |
| **CPU Usage** | < 60% | > 80% | Scale Cloud Run instances |

### Monitoring Dashboards

**Cloud Console > Monitoring > Dashboards**

Create dashboard with panels for:
1. Request rate (requests/second)
2. Error rate (%)
3. Response latency (p50, p95, p99)
4. Instance count
5. Memory usage
6. CPU usage
7. Database connections

### Alert Policies

```bash
# High error rate alert
gcloud alpha monitoring policies create \
  --display-name="Python Backend - High Error Rate" \
  --condition-threshold-value=0.01 \
  --condition-threshold-duration=300s \
  --notification-channels=EMAIL_CHANNEL_ID

# High latency alert
gcloud alpha monitoring policies create \
  --display-name="Python Backend - High Latency" \
  --condition-threshold-value=500 \
  --condition-threshold-duration=600s \
  --notification-channels=EMAIL_CHANNEL_ID

# Low health check success rate
gcloud alpha monitoring policies create \
  --display-name="Python Backend - Health Check Failures" \
  --condition-threshold-value=0.95 \
  --condition-threshold-duration=180s \
  --notification-channels=EMAIL_CHANNEL_ID,PAGERDUTY_CHANNEL_ID
```

### Log Monitoring

**Important Log Queries:**

```bash
# Errors in last hour
gcloud logging read 'resource.type="cloud_run_revision"
  resource.labels.service_name="liftlog-python-backend-staging"
  severity>=ERROR
  timestamp>="2024-01-01T00:00:00Z"' \
  --limit=50 --format=json

# Slow requests (> 1 second)
gcloud logging read 'resource.type="cloud_run_revision"
  jsonPayload.duration_ms>1000
  timestamp>="2024-01-01T00:00:00Z"' \
  --limit=50

# Failed authentication attempts
gcloud logging read 'resource.type="cloud_run_revision"
  jsonPayload.error_type="AuthenticationError"' \
  --limit=50
```

---

## 🔧 Troubleshooting Guide

### Issue: Service Won't Start

**Symptoms:**
- Cloud Run shows "Service Unavailable"
- Health check failing
- Logs show startup errors

**Investigation Steps:**

1. Check logs:
   ```bash
   gcloud run logs tail liftlog-python-backend-staging \
     --region=us-central1 --limit=100
   ```

2. Look for common issues:
   - Database connection errors
   - Secret access denied
   - Missing environment variables
   - Import errors

3. Verify environment variables:
   ```bash
   gcloud run services describe liftlog-python-backend-staging \
     --region=us-central1 \
     --format='value(spec.template.spec.containers[0].env)'
   ```

4. Test database connectivity:
   ```bash
   gcloud sql instances describe liftlog-user-data-staging
   # Check status is RUNNABLE
   ```

**Resolution:**
- If database issue: Check connection string, credentials
- If secret issue: Verify service account has `secretmanager.secretAccessor` role
- If code issue: Rollback to previous version

### Issue: High Error Rate (5xx)

**Symptoms:**
- Monitoring shows error rate > 1%
- Users reporting failures

**Investigation Steps:**

1. Check error logs:
   ```bash
   gcloud logging read 'severity>=ERROR' --limit=20 --format=json
   ```

2. Identify error patterns:
   - Database timeouts?
   - External API failures (OpenAI)?
   - Memory errors?

3. Check resource usage:
   ```bash
   # View Cloud Run metrics
   # Console > Cloud Run > Service > Metrics
   ```

**Resolution:**
- Database timeouts: Increase connection pool size or scale database
- Memory errors: Increase Cloud Run memory allocation
- External API: Check API status, implement circuit breaker

### Issue: Slow Response Times

**Symptoms:**
- p95 latency > 500ms
- p99 latency > 1000ms

**Investigation Steps:**

1. Check metrics endpoint:
   ```bash
   curl $SERVICE_URL/metrics
   ```

2. Identify slowest endpoints
3. Check database query performance:
   ```bash
   # Cloud SQL > Query Insights
   ```

4. Check external API latencies (OpenAI)

**Resolution:**
- Add database indexes
- Optimize queries
- Implement caching
- Increase Cloud Run CPU

### Issue: Database Connection Pool Exhausted

**Symptoms:**
- Logs show "connection pool exhausted"
- Intermittent 5xx errors

**Investigation Steps:**

1. Check current pool configuration:
   ```python
   # In app/db/session.py
   # pool_size, max_overflow
   ```

2. Monitor active connections:
   ```bash
   # Cloud SQL > Monitoring > Connections
   ```

**Resolution:**
- Increase `pool_size` and `max_overflow` in database config
- Add connection timeout handling
- Implement connection retry logic
- Scale database instance if needed

---

## 🚨 Incident Response

### Severity Levels

| Level | Definition | Response Time | Escalation |
|-------|-----------|---------------|------------|
| **P0 - Critical** | Service completely down | Immediate | On-call + Manager |
| **P1 - High** | Partial outage, > 5% errors | < 15 min | On-call |
| **P2 - Medium** | Degraded performance | < 1 hour | Normal |
| **P3 - Low** | Minor issues, no user impact | < 24 hours | Normal |

### Incident Response Procedure

1. **Acknowledge the incident**
   - Post in incident channel
   - Assign incident commander

2. **Assess severity**
   - Check error rates
   - Check user impact
   - Determine severity level

3. **Immediate actions**
   - If P0/P1: Consider rollback
   - Start investigation
   - Communicate status

4. **Investigation**
   - Check recent deployments
   - Review logs and metrics
   - Identify root cause

5. **Resolution**
   - Apply fix or rollback
   - Verify resolution
   - Monitor for 30 minutes

6. **Post-incident**
   - Write post-mortem
   - Identify action items
   - Update runbooks

### Communication Template

```
**INCIDENT ALERT**
Severity: [P0/P1/P2/P3]
Status: [Investigating/Identified/Monitoring/Resolved]
Impact: [Description of user impact]
Started: [Timestamp]

**Current Status:**
[Brief description of what's happening]

**Actions Taken:**
- [Action 1]
- [Action 2]

**Next Steps:**
- [Next step 1]
- [Next step 2]

**ETA to Resolution:** [Estimate]
```

---

## 🔧 Maintenance Procedures

### Database Backup and Restore

**Manual Backup:**
```bash
gcloud sql backups create \
  --instance=liftlog-user-data-staging \
  --description="Manual backup before major change"
```

**Restore from Backup:**
```bash
# List backups
gcloud sql backups list --instance=liftlog-user-data-staging

# Restore
gcloud sql backups restore BACKUP_ID \
  --backup-instance=liftlog-user-data-staging
```

### Rotating Secrets

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# 2. Add new version to Secret Manager
echo -n "$NEW_SECRET" | \
  gcloud secrets versions add web-auth-api-key-staging --data-file=-

# 3. Deploy new revision (will automatically use latest secret version)
./infrastructure/scripts/deploy.sh staging latest

# 4. Verify new revision is working
curl $SERVICE_URL/health

# 5. Disable old secret version (after verification)
gcloud secrets versions disable 1 --secret=web-auth-api-key-staging
```

### Scaling Operations

**Manual Scaling:**
```bash
# Update max instances
gcloud run services update liftlog-python-backend-staging \
  --region=us-central1 \
  --max-instances=20

# Update CPU/memory
gcloud run services update liftlog-python-backend-staging \
  --region=us-central1 \
  --cpu=2 \
  --memory=4Gi
```

**Database Scaling:**
```bash
# Increase database tier
gcloud sql instances patch liftlog-user-data-staging \
  --tier=db-custom-4-15360

# Enable high availability (for production)
gcloud sql instances patch liftlog-user-data-production \
  --availability-type=REGIONAL
```

### Cleanup Tasks

The backend automatically runs cleanup tasks hourly to:
- Delete expired user events (> 30 days old)
- Delete expired shared items

**Manual cleanup:**
```bash
# Trigger cleanup via API (future feature)
# Or connect to database and run manual cleanup
```

---

## 📝 Deployment Checklist

### Before Deployment
- [ ] Tests passing
- [ ] Code reviewed and approved
- [ ] CHANGELOG updated
- [ ] Team notified
- [ ] Maintenance window scheduled (if needed)
- [ ] Rollback plan prepared

### During Deployment
- [ ] Deployment initiated
- [ ] Deployment logs monitored
- [ ] Health checks passing
- [ ] Smoke tests completed
- [ ] Metrics reviewed

### After Deployment
- [ ] Monitor error rates for 30 minutes
- [ ] Check performance metrics
- [ ] Review logs for warnings
- [ ] Update deployment documentation
- [ ] Notify team of completion

---

## 📚 Additional Resources

- [Infrastructure README](infrastructure/README.md)
- [Migration Roadmap](MIGRATION_ROADMAP.md)
- [Main README](README.md)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)

---

**Last Updated:** 2025-11-23
**Maintained By:** DevOps Team
**Review Schedule:** Quarterly
