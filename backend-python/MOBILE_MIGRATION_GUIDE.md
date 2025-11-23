# Mobile Client Migration Guide

This guide provides instructions for migrating the LiftLog mobile applications (iOS and Android) from the C# backend to the Python/FastAPI backend.

## 📋 Overview

**Migration Strategy:** Gradual rollout with feature flags

- **Phase 1:** Internal testing (0% of users)
- **Phase 2:** Beta testing (10% of users)
- **Phase 3:** Gradual rollout (25% → 50% → 75%)
- **Phase 4:** Full migration (100%)
- **Phase 5:** C# backend decommissioning

---

## 🔄 API Changes

### Endpoint URL Changes

The Python backend uses `/v2/` prefix for all API endpoints:

| C# Endpoint (v1) | Python Endpoint (v2) | Notes |
|-----------------|---------------------|-------|
| `/user/create` | `/v2/user/create` | ✅ Identical behavior |
| `/user/{id}` | `/v2/user/{id}` | ✅ Identical behavior |
| `/user` | `/v2/user` | ✅ Identical behavior |
| `/user/delete` | `/v2/user/delete` | ✅ Identical behavior |
| `/users` | `/v2/users` | ✅ Identical behavior |
| `/event` | `/v2/event` | ✅ Identical behavior |
| `/events` | `/v2/events` | ✅ Identical behavior |
| `/follow-secret` | `/v2/follow-secret` | ✅ Identical behavior |
| `/follow-secret/delete` | `/v2/follow-secret/delete` | ✅ Identical behavior |
| `/inbox` (PUT) | `/v2/inbox` (PUT) | ✅ Identical behavior |
| `/inbox` (POST) | `/v2/inbox` (POST) | ✅ Identical behavior |
| `/shareditem` | `/v2/shareditem` | ✅ Identical behavior |
| `/shareditem/{id}` | `/v2/shareditem/{id}` | ✅ Identical behavior |
| `/ai/workout` | `/v2/ai/workout` | ✅ Identical behavior |
| `/ai/session` | `/v2/ai/session` | ✅ Identical behavior |
| `/ai-chat` | `/ai-chat` | ⚠️ **No `/v2` prefix** |
| `/health` | `/health` | ⚠️ **No `/v2` prefix** |

### Important Notes

1. **All API endpoints use `/v2/` prefix EXCEPT:**
   - WebSocket endpoint: `/ai-chat` (no prefix)
   - Health check: `/health` (no prefix)

2. **Request/Response formats are identical** between v1 and v2
3. **Authentication headers are identical** (same password-based auth)
4. **All encryption/decryption logic remains the same**

---

**Last Updated:** 2025-11-23
**Contact:** DevOps Team
**Status:** Ready for Implementation
