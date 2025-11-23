# LiftLog C# → Python/FastAPI Migration Roadmap

## ✅ Phase 1: Foundation (COMPLETED)

### Project Setup
- [x] Initialize Python project with uv
- [x] Configure pyproject.toml with dependencies
- [x] Set up directory structure
- [x] Create .env.example and configuration

### Database Layer
- [x] SQLModel User model
- [x] SQLModel UserEvent model
- [x] SQLModel UserFollowSecret model
- [x] SQLModel UserInboxItem model
- [x] SQLModel SharedItem model
- [x] SQLModel RateLimitConsumption model
- [x] Database session management (async)
- [x] Alembic configuration
- [x] Two-database setup (user_data + rate_limit)

### Pydantic Schemas
- [x] User schemas (Create, Get, Put, Delete, GetUsers)
- [x] Event schemas (PutEvent, GetEvents)
- [x] Follow schemas (Put, Delete)
- [x] Inbox schemas (Put, Get)
- [x] Shared item schemas (Post, Get)
- [x] AI workout schemas (GenerateWorkout, GenerateSession)

### Core Services
- [x] PasswordService with PBKDF2-SHA512
- [x] Configuration management (Settings)
- [x] Enums (AppStore, ExperienceLevel)
- [x] Custom exceptions

### API Endpoints - User Management
- [x] POST /v2/user/create
- [x] GET /v2/user/{idOrLookup}
- [x] PUT /v2/user
- [x] POST /v2/user/delete
- [x] POST /v2/users (batch)
- [x] GET /health

### Testing
- [x] pytest configuration
- [x] Test fixtures with async database
- [x] User endpoint tests (create, get, put, delete)
- [x] PasswordService unit tests

### DevOps
- [x] Dockerfile (multi-stage)
- [x] .dockerignore
- [x] .gitignore
- [x] README.md with documentation

---

## 🔄 Phase 2: Authentication & Security (NEXT)

### Purchase Verification Services
- [ ] Base PurchaseVerificationService interface
- [ ] GooglePlayPurchaseVerification implementation
- [ ] AppleAppStorePurchaseVerification implementation
- [ ] RevenueCatPurchaseVerification implementation
- [ ] WebAuthPurchaseVerification implementation
- [ ] Purchase token caching/validation

### Authentication Middleware
- [ ] FastAPI dependency for purchase token extraction
- [ ] WebSocket purchase token verification
- [ ] Password authentication helpers
- [ ] Auth context (AppStore, ProToken)

### Rate Limiting
- [ ] RateLimitService implementation
- [ ] SHA256 token hashing
- [ ] Per-store rate limits (Web: 100/day, Mobile: 20/day)
- [ ] TEST_MODE bypass logic
- [ ] Retry-After header handling

### Testing
- [ ] Purchase verification tests
- [ ] Rate limiting tests
- [ ] Authentication middleware tests

**Estimated Time:** 3-4 days

---

## 📅 Phase 3: Remaining API Endpoints (PENDING)

### Event Routes
- [ ] PUT /v2/event - Create/update event
- [ ] POST /v2/events - Get events from followed users
- [ ] Follow secret validation logic
- [ ] Event expiry handling

### Social Routes
- [ ] PUT /v2/follow-secret - Create follow token
- [ ] POST /v2/follow-secret/delete - Revoke follow token
- [ ] PUT /v2/inbox - Send encrypted message
- [ ] POST /v2/inbox - Get and clear messages
- [ ] RSA message chunking/decryption

### Sharing Routes
- [ ] POST /v2/shareditem - Create shareable item
- [ ] GET /v2/shareditem/{id} - Get shared item
- [ ] CUID generation for IDs
- [ ] Expiry validation

### Testing
- [ ] Event endpoint tests
- [ ] Social endpoint tests
- [ ] Sharing endpoint tests
- [ ] Integration tests for cross-feature workflows

**Estimated Time:** 4-5 days

---

## 🤖 Phase 4: AI Integration (PENDING)

### OpenAI Service
- [ ] GptAiWorkoutPlanner implementation
- [ ] GPT-4o configuration
- [ ] Function calling for structured output
- [ ] Prompt engineering (workout plans)
- [ ] Prompt engineering (sessions)
- [ ] Error handling and retries

### AI Routes
- [ ] POST /v2/ai/workout - Generate workout plan
- [ ] POST /v2/ai/session - Generate session
- [ ] Purchase token auth requirement
- [ ] Rate limit integration

### WebSocket Chat
- [ ] GptChatWorkoutPlanner service
- [ ] WebSocket endpoint at /ai-chat
- [ ] Connection state management
- [ ] Streaming GPT responses
- [ ] Stop/restart functionality
- [ ] Cleanup on disconnect
- [ ] SignalR-compatible message format

### Testing
- [ ] AI planner unit tests
- [ ] AI endpoint integration tests
- [ ] WebSocket connection tests
- [ ] Chat flow tests

**Estimated Time:** 5-6 days

---

## 🔧 Phase 5: Background Services & Optimization (PENDING)

### Background Tasks
- [ ] CleanupExpiredDataService implementation
- [ ] APScheduler configuration (hourly)
- [ ] Expired event deletion logic
- [ ] Logging and monitoring

### Performance Optimization
- [ ] Database query optimization
- [ ] Connection pooling tuning
- [ ] Caching strategy (Redis?)
- [ ] API response compression

### Monitoring & Logging
- [ ] Structured logging setup
- [ ] Error tracking integration
- [ ] Performance metrics
- [ ] Health check enhancements

### Testing
- [ ] Background task tests
- [ ] Load testing
- [ ] Performance benchmarks

**Estimated Time:** 2-3 days

---

## 🚀 Phase 6: Deployment & Migration (PENDING)

### Deployment Preparation
- [ ] Environment-specific configs (dev, staging, prod)
- [ ] Secrets management (Google Secret Manager?)
- [ ] Docker Compose for local dev
- [ ] CI/CD pipeline setup
- [ ] Database backup strategy

### Google Cloud Deployment
- [ ] Google Cloud Run setup
- [ ] Cloud SQL PostgreSQL instances
- [ ] Load balancer configuration
- [ ] SSL/TLS certificates
- [ ] Environment variables setup

### Data Migration
- [ ] Migration scripts from C# schema (if needed)
- [ ] Data integrity validation
- [ ] Rollback plan

### Parallel Deployment
- [ ] Deploy Python API as v2
- [ ] Run C# and Python APIs in parallel
- [ ] Traffic splitting/canary deployment
- [ ] Monitor error rates
- [ ] Performance comparison

### Client Migration
- [ ] Update mobile apps to use v2 endpoints
- [ ] Gradual rollout (A/B testing)
- [ ] Fallback to v1 if issues

### Decommissioning
- [ ] Full migration verification
- [ ] Decommission C# API
- [ ] Clean up old infrastructure
- [ ] Update documentation

### Testing
- [ ] End-to-end tests in staging
- [ ] Load testing in production-like environment
- [ ] Security audit
- [ ] Penetration testing

**Estimated Time:** 5-7 days

---

## 📊 Progress Tracking

| Phase | Status | Progress | Est. Time | Actual Time |
|-------|--------|----------|-----------|-------------|
| Phase 1: Foundation | ✅ Complete | 100% | 5-7 days | - |
| Phase 2: Auth & Security | ⏳ Next | 0% | 3-4 days | - |
| Phase 3: API Endpoints | 📋 Pending | 0% | 4-5 days | - |
| Phase 4: AI Integration | 📋 Pending | 0% | 5-6 days | - |
| Phase 5: Background Services | 📋 Pending | 0% | 2-3 days | - |
| Phase 6: Deployment | 📋 Pending | 0% | 5-7 days | - |

**Total Estimated Time:** 24-32 days

---

## 🎯 Current Focus: Phase 2 - Authentication & Security

### Immediate Next Steps

1. **Create purchase verification service interface**
   - Define abstract base class
   - Common verification response model
   - Error handling patterns

2. **Implement Google Play verification**
   - Google API client setup
   - Receipt validation logic
   - Token caching

3. **Implement Apple App Store verification**
   - Apple receipt validation
   - Shared secret configuration
   - Sandbox vs production handling

4. **Implement RevenueCat verification**
   - HTTP client setup
   - API key authentication
   - Subscription validation

5. **Create FastAPI authentication dependency**
   - Extract purchase token from Authorization header
   - Validate with appropriate service
   - Create user claims/context

6. **Implement rate limiting service**
   - SHA256 token hashing
   - Sliding window algorithm
   - Per-store limit enforcement

### Files to Create Next

```
app/services/purchase_verification/
├── __init__.py
├── base.py                    # Abstract base class
├── google_play.py             # Google Play verification
├── apple.py                   # Apple App Store verification
├── revenuecat.py              # RevenueCat verification
└── web_auth.py                # Web authentication

app/auth/
├── purchase_token.py          # FastAPI dependency
└── password.py                # Password auth helpers

app/services/
└── rate_limit.py              # Rate limiting service

tests/test_services/
├── test_purchase_verification.py
└── test_rate_limit.py
```

---

## 🔍 Quality Checklist

Before moving to next phase:

- [ ] All tests passing
- [ ] Code coverage > 80%
- [ ] Type hints on all functions
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Performance benchmarks met
- [ ] Code review completed

---

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Google Play Developer API](https://developers.google.com/android-publisher)
- [Apple App Store Server API](https://developer.apple.com/documentation/appstoreserverapi)
- [RevenueCat API](https://docs.revenuecat.com/)
- [OpenAI API](https://platform.openai.com/docs)

---

**Last Updated:** 2025-11-23
