# CLAUDE.md - AI Assistant Guide for LiftLog

This document provides comprehensive guidance for AI assistants working with the LiftLog codebase. Last updated: 2025-11-23

## Table of Contents

- [Project Overview](#project-overview)
- [Repository Structure](#repository-structure)
- [Tech Stack](#tech-stack)
- [Development Workflows](#development-workflows)
- [Code Conventions](#code-conventions)
- [Testing](#testing)
- [Architecture Patterns](#architecture-patterns)
- [Important Constraints](#important-constraints)
- [Common Tasks](#common-tasks)

---

## Project Overview

**LiftLog** is a privacy-first, cross-platform gym weight tracking app with the following key features:

- **Multi-platform**: Android, iOS, and Web (React Native + Expo)
- **AI-powered**: GPT-4o workout plan generation
- **End-to-end encrypted**: Social feeds with RSA + AES encryption
- **Internationalized**: 11 languages via Tolgee
- **Material Design 3**: Modern UI via React Native Paper
- **In-app purchases**: RevenueCat integration

### Current State

- **Backend Migration**: Migrating from C# (.NET) to Python (FastAPI) - 83% complete
  - Backend development: 100% complete
  - Deployment phase: In progress
  - Both backends currently operational (C# at root endpoints, Python at `/v2/`)

---

## Repository Structure

```
LiftLog/
├── app/                          # React Native/Expo frontend (main app)
│   ├── app/                      # Expo Router file-based routes
│   │   ├── (tabs)/              # Tab navigation (session, feed, history, settings, stats)
│   │   └── _layout.tsx          # Root layout
│   ├── components/              # React components
│   │   ├── layout/             # Page structure components
│   │   ├── presentation/       # Dumb/presentational components
│   │   └── smart/              # Smart/container components (Redux-connected)
│   ├── store/                   # Redux Toolkit state management
│   │   ├── current-session/    # Active workout state
│   │   ├── program/            # Training program state
│   │   ├── feed/               # Social feed state
│   │   ├── settings/           # App settings
│   │   ├── ai-planner/         # AI workout planner
│   │   ├── stats/              # Statistics
│   │   └── store.ts            # Store configuration
│   ├── services/                # Business logic layer
│   ├── models/                  # TypeScript type definitions
│   ├── hooks/                   # Custom React hooks
│   ├── utils/                   # Utility functions
│   ├── i18n/                    # Translation files (11 languages)
│   ├── gen/                     # Generated Protocol Buffer code
│   ├── android/                 # Android native code (Kotlin)
│   ├── ios/                     # iOS native code
│   └── test/                    # Test setup
│
├── backend/                     # C# .NET 9.0 backend (original)
│   ├── LiftLog.Api/            # ASP.NET Core Web API
│   │   ├── Controllers/        # API endpoints
│   │   ├── Models/             # Entity models
│   │   ├── Db/                 # Database contexts (2 DBs: UserData, RateLimit)
│   │   ├── Service/            # Business logic
│   │   ├── Hubs/               # SignalR WebSocket hubs
│   │   └── Migrations/         # EF Core migrations
│   ├── LiftLog.Lib/            # Shared library
│   └── RevenueCat/             # RevenueCat integration
│
├── backend-python/              # Python FastAPI backend (new, v2 API)
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/         # API endpoint routers
│   │   │   └── websockets/     # WebSocket handlers
│   │   ├── models/
│   │   │   ├── database/       # SQLModel ORM models
│   │   │   └── schemas/        # Pydantic request/response schemas
│   │   ├── services/           # Business logic
│   │   ├── auth/               # Authentication
│   │   ├── db/                 # Database session management
│   │   └── core/               # Configuration
│   ├── tests/                  # pytest tests
│   └── alembic/                # Database migrations
│
├── proto/                       # Protocol Buffer definitions (.proto files)
├── site/                        # Marketing website (Bootstrap + Pug)
├── tests/                       # Test suites
│   ├── LiftLog.Tests.Api/      # C# API integration tests (xUnit)
│   └── cypress-tests/          # E2E tests (Cypress)
├── scripts/                     # Build/release automation
├── docs/                        # Documentation
│   ├── FeedProcess.md          # End-to-end encryption details
│   ├── RemoteBackup.md         # Remote backup system
│   └── PlaintextExport.md      # Data export format
└── examples/                    # Example configurations
```

---

## Tech Stack

### Frontend (`/app/`)

| Category | Technology | Version |
|----------|-----------|---------|
| **Framework** | React Native | 0.81.4 |
| | React | 19.1.0 |
| | Expo SDK | 54 |
| | TypeScript | 5.9.2 |
| **UI** | React Native Paper (Material Design 3) | 5.14.5 |
| | React Native Reanimated | 4.1.1 |
| | React Native Gesture Handler | 2.28.0 |
| | @shopify/flash-list | 2.0.2 |
| **State** | Redux Toolkit | 2.6.1 |
| | Redux Listener Middleware | (built-in) |
| **i18n** | Tolgee React | 6.2.2 |
| **Data** | Protocol Buffers (protobufjs) | 7.5.0 |
| **Real-time** | @microsoft/signalr | 9.0.0 |
| **Purchases** | react-native-purchases (RevenueCat) | 9.4.2 |
| **Testing** | Vitest | 3.1.1 |
| | jsdom | 26.1.0 |
| **Build** | Metro (Expo's bundler) | - |
| | Babel (preset-expo) | - |

### Backend - C# (`/backend/`)

| Category | Technology | Version |
|----------|-----------|---------|
| **Framework** | .NET | 9.0 |
| | ASP.NET Core Web API | 9.0 |
| **Database** | PostgreSQL | 17 |
| | Entity Framework Core | 9.0 |
| | Npgsql EF Provider | 9.0.4 |
| **Security** | FluentValidation | 12.1.0 |
| | PBKDF2-SHA512 | 350k iterations |
| **AI** | OpenAI SDK | 2.6.0 |
| **Formatting** | CSharpier | 1.1.2 |

### Backend - Python (`/backend-python/`)

| Category | Technology | Version |
|----------|-----------|---------|
| **Framework** | FastAPI | 0.115+ |
| | Uvicorn | 0.32.0+ |
| | Python | 3.12+ |
| **Database** | PostgreSQL | 14+ |
| | SQLModel | 0.0.22 |
| | asyncpg | 0.30.0 |
| | Alembic | 1.14.0 |
| **Security** | Cryptography | 44.0.0 |
| | Passlib (bcrypt) | 1.7.4+ |
| | python-jose | 3.3.0+ |
| **AI** | OpenAI SDK | 1.58.1+ |
| **Package Manager** | uv | latest |
| **Code Quality** | Ruff | 0.8.4+ |
| | mypy (strict) | 1.13.0+ |
| | pytest | 8.3.4+ |

---

## Development Workflows

### Frontend Development

```bash
cd app
npm install                    # Install dependencies
npm start                      # Start Expo dev server
npm run android               # Run on Android
npm run ios                   # Run on iOS (macOS only)
npm run web                   # Run in browser
npm run lint                  # Run ESLint
npm test                      # Run Vitest tests
npm run typecheck             # TypeScript type check
npm run proto                 # Generate Protocol Buffer code from .proto files
npm run pull-translations     # Pull translations from Tolgee
```

**Important Notes**:
- Always run `npm run proto` after modifying `.proto` files
- Use `@/` path alias for imports (maps to `./`)
- Platform-specific code uses `.native.ts` suffix

### Backend Development (C#)

```bash
cd backend/LiftLog.Api
dotnet restore                # Restore dependencies
dotnet build                  # Build solution
dotnet test                   # Run tests
dotnet csharpier .           # Format code (REQUIRED before commits)
dotnet run                    # Run API locally (default: http://localhost:5000)
```

### Backend Development (Python)

```bash
cd backend-python
uv sync                       # Install dependencies
uv run pytest                 # Run tests
uv run ruff format .         # Format code
uv run ruff check .          # Lint code
uv run mypy app              # Type check
uv run alembic upgrade head  # Run migrations
uv run uvicorn app.main:app --reload  # Run dev server
```

### Release Process

Releases are automated via GitHub Actions:

1. Create GitHub release with tag (e.g., `v1.2.3`)
2. Workflows automatically:
   - Build Android AAB/APK → Upload to Google Play (internal track)
   - Build iOS app → Upload to TestFlight
   - Build web app → Deploy to hosting
   - Build/deploy API to production

**Scripts** (`/scripts/`):
- `create-release.ts` - Create GitHub releases
- `get-release-notes.ts` - Generate changelog
- `collect-screenshots.ts` - Gather app screenshots

---

## Code Conventions

### TypeScript/JavaScript

**Style Rules** (`.eslintrc.js`, `.prettierrc`):
- **Single quotes** for strings
- **Semicolons required**
- **Trailing commas** everywhere
- **2-space indentation**
- **Strict TypeScript** mode with `exactOptionalPropertyTypes: true`

**Import Restrictions** (enforced by ESLint):

```typescript
// ❌ WRONG - Don't use these
import { useSelector } from 'react-redux';
import { IconButton } from 'react-native-paper';
import * from '@material-symbols-react-native/outlined-400';

// ✅ CORRECT - Use these instead
import { useAppSelector } from '@/store';
import { IconButton } from '@/components/presentation/gesture-wrappers';
import MenuIcon from '@material-symbols-react-native/outlined-400/Menu'; // Individual imports only
```

**Naming Conventions**:
- Components: `PascalCase`
- Files: `kebab-case` for utilities, `PascalCase` for components
- Routes: `kebab-case` with `()` for route groups (e.g., `app/(tabs)/feed/index.tsx`)
- Constants: `UPPER_SNAKE_CASE`
- Platform-specific: `*.native.ts` suffix

**Path Aliases**:
```typescript
import { SessionModel } from '@/models/session-models';  // ✅ Preferred
import { SessionModel } from '../models/session-models'; // ❌ Avoid relative paths
```

### C#

**Style Rules**:
- **PascalCase** for everything (classes, methods, properties, public fields)
- **camelCase** for private fields
- **Async methods** must have `Async` suffix
- **Format with CSharpier** before every commit
- **Database naming**: `snake_case` (via `EFCore.NamingConventions`)

```csharp
// ✅ CORRECT
public async Task<User> GetUserAsync(string userId)
{
    return await _context.Users.FindAsync(userId);
}
```

**Important**:
- Run `dotnet csharpier .` before committing
- Treat warnings as errors (enabled in project)
- Nullable reference types enabled

### Python

**Style Rules** (PEP 8 + Ruff):
- **snake_case** for everything (functions, variables, files)
- **PascalCase** for classes
- **Line length**: 100 characters
- **Type hints required** (mypy strict mode)
- **Async/await** for all I/O operations

```python
# ✅ CORRECT
async def get_user(user_id: str) -> User | None:
    async with get_session() as session:
        result = await session.get(User, user_id)
        return result
```

---

## Testing

### Frontend Tests (Vitest)

**Location**: Co-located with source files (`.spec.ts` next to implementation)

```bash
app/services/encryption-service.ts
app/services/encryption-service.spec.ts  # ✅ Test file here
```

**Running Tests**:
```bash
npm test                      # Run all tests
npm test -- --watch          # Watch mode
npm test -- encryption       # Run specific test
```

**Configuration**: `vitest.config.ts`
- Environment: `jsdom`
- Setup file: `./test/setup.ts`
- Path resolution via `vite-tsconfig-paths`

### Backend Tests (C#)

**Framework**: xUnit
**Location**: `/tests/LiftLog.Tests.Api/`

```bash
dotnet test                   # Run all tests
```

**Notes**:
- Uses ASP.NET Core `TestServer` for integration tests
- Requires PostgreSQL test database
- Connection strings via environment variables

### Backend Tests (Python)

**Framework**: pytest
**Location**: `/backend-python/tests/`

```bash
uv run pytest                 # Run all tests
uv run pytest -v             # Verbose
uv run pytest --cov          # With coverage
```

**Configuration**: `pyproject.toml`
- Async tests: `pytest-asyncio`
- Coverage: `pytest-cov`

### E2E Tests (Cypress)

**Location**: `/tests/cypress-tests/`

Tests full stack (frontend + backend together).

---

## Architecture Patterns

### Frontend State Management (Redux)

**Structure**:
```
store/
├── current-session/
│   ├── index.ts          # Reducer + actions
│   └── effects.ts        # Side effects (listener middleware)
├── settings/
│   ├── index.ts
│   └── effects.ts
└── store.ts              # Store configuration
```

**Key Patterns**:

1. **Use Redux Listener Middleware for side effects** (NOT thunks):

```typescript
import { startAppListening } from '@/store/store';
import { actionCreated } from './index';

startAppListening({
  actionCreator: actionCreated,
  effect: async (action, listenerApi) => {
    const { extra, getState, dispatch } = listenerApi;
    // extra is Services (injected dependencies)
    const user = await extra.feedApi.getUser();
    dispatch(userLoaded(user));
  },
});
```

2. **Services injected via `extra` parameter**:
   - `extra.feedApi` - Feed API service
   - `extra.encryptionService` - Encryption service
   - `extra.keyValueStore` - Persistence service

3. **Manual persistence** (no redux-persist):
   - Data serialized to Protocol Buffers
   - Stored via `keyValueStore` abstraction

4. **Debounced effects** for performance:

```typescript
startAppListening({
  actionCreator: settingChanged,
  effect: debounce(async (action, listenerApi) => {
    await listenerApi.extra.keyValueStore.set('settings', serialize(action.payload));
  }, 1000),
});
```

### Backend Architecture (C#)

**Layered Architecture**:
- **Controllers**: HTTP endpoints (thin, delegate to services)
- **Services**: Business logic
- **Models**: Domain entities (EF Core)
- **Db**: Database contexts (2 separate: `UserDataContext`, `RateLimitContext`)
- **Validators**: FluentValidation input validation
- **Hubs**: SignalR WebSocket hubs

### Backend Architecture (Python)

**Clean Architecture**:
- **Routes** (`api/routes/`): API endpoint definitions
- **Schemas** (`models/schemas/`): Pydantic request/response models
- **Database Models** (`models/database/`): SQLModel ORM entities
- **Services** (`services/`): Business logic
- **Auth** (`auth/`): Authentication handlers
- **Core** (`core/`): Configuration

**API Versioning**:
- Original C# endpoints: Root path (e.g., `/api/user`)
- New Python endpoints: `/v2/` prefix (e.g., `/v2/user`)

---

## Important Constraints

### Security & Privacy

**End-to-End Encryption** (see `/docs/FeedProcess.md`):

1. **User Identity** (stored on device):
   - AES-128 key for payload encryption
   - RSA-2048 keypair for key exchange & signatures
   - UUID user ID
   - Password (for server authentication)

2. **Feed Publishing**:
   - Payload signed with RSA private key (RSA-PSS)
   - Payload + signature encrypted with AES-128 (CBC mode)
   - Server stores encrypted payload + IV (NEVER the keys)

3. **Following Process**:
   - Follower requests via RSA-encrypted inbox message
   - Original user approves and shares AES key via RSA encryption
   - Follower decrypts feed items with shared AES key
   - Signature verification ensures authenticity

**CRITICAL**:
- **NEVER** expose private keys in logs, errors, or API responses
- **ALWAYS** validate signatures after decryption
- **NEVER** store unencrypted sensitive data on server
- Password hashing: PBKDF2-SHA512 with 350,000 iterations

### Protocol Buffers

**All persisted data MUST use Protocol Buffers**:

1. Define schema in `/proto/*.proto`
2. Generate code: `npm run proto` (in `app/`)
3. Use generated types from `@/gen/proto`

```typescript
import { proto } from '@/gen/proto';

// ✅ CORRECT - Use Protocol Buffers
const session = proto.Session.create({ ... });
const bytes = proto.Session.encode(session).finish();
await keyValueStore.set('current-session', bytes);

// ❌ WRONG - Don't use JSON for persistence
localStorage.setItem('session', JSON.stringify(session));
```

**Why?**:
- Forward/backward compatibility
- Efficient binary serialization
- Type safety across platforms

### Import Restrictions

**Enforced by ESLint** - these will cause build failures:

```typescript
// ❌ WRONG - Will fail CI
import { useSelector } from 'react-redux';
import { IconButton, Button, TouchableRipple } from 'react-native-paper';
import * as Icons from '@material-symbols-react-native/outlined-400';

// ✅ CORRECT
import { useAppSelector } from '@/store';
import { IconButton, Button, TouchableRipple } from '@/components/presentation/gesture-wrappers';
import MenuIcon from '@material-symbols-react-native/outlined-400/Menu';
```

**Reason**:
- `useAppSelector` has correct typing for our store
- Gesture wrappers use React Native Gesture Handler (more reliable)
- Bulk material icon imports crash Android (too large)

### Multi-Platform Considerations

**Platform-specific code**:

```typescript
// services/key-value-store.ts       - Interface
// services/key-value-store.native.ts - iOS/Android implementation
// services/key-value-store.web.ts    - Web implementation
```

**Metro bundler automatically picks correct file**:
- Android/iOS: Uses `.native.ts`
- Web: Uses `.web.ts`
- Fallback: Uses base `.ts`

---

## Common Tasks

### Adding a New Feature

1. **Plan the feature**:
   - Identify affected components (frontend/backend/both)
   - Consider Protocol Buffer schema changes
   - Plan state management (Redux slices)

2. **Frontend changes**:
   ```bash
   # If data model changes:
   # 1. Update .proto files
   npm run proto

   # 2. Create Redux slice
   # app/store/new-feature/index.ts
   # app/store/new-feature/effects.ts

   # 3. Create components
   # app/components/presentation/NewFeature.tsx

   # 4. Add route
   # app/app/(tabs)/new-feature/index.tsx

   # 5. Add tests
   # *.spec.ts files co-located with source

   # 6. Run tests and lint
   npm test
   npm run lint
   npm run typecheck
   ```

3. **Backend changes (Python preferred for new features)**:
   ```bash
   cd backend-python

   # 1. Add database model
   # app/models/database/new_model.py

   # 2. Create migration
   uv run alembic revision --autogenerate -m "Add new feature"
   uv run alembic upgrade head

   # 3. Add Pydantic schemas
   # app/models/schemas/new_schema.py

   # 4. Add service
   # app/services/new_service.py

   # 5. Add route
   # app/api/routes/new_route.py

   # 6. Add tests
   # tests/test_new_feature.py

   # 7. Run tests and checks
   uv run pytest
   uv run ruff format .
   uv run ruff check .
   uv run mypy app
   ```

### Modifying Protocol Buffers

**IMPORTANT**: Protocol Buffers ensure backward compatibility. Follow these rules:

1. **NEVER** remove or rename fields
2. **NEVER** change field types
3. **DO** add new optional fields
4. **DO** use reserved field numbers for deleted fields

```protobuf
message Session {
  string id = 1;
  int64 date = 2;
  // reserved 3;  // Old field removed - mark as reserved
  repeated Exercise exercises = 4;
  optional string notes = 5;  // ✅ New optional field OK
}
```

5. After changes:
```bash
cd app
npm run proto  # Regenerate code
git add gen/proto.js gen/proto.d.ts
```

### Adding Translations

1. **Add key to English** (`app/i18n/en.json`):
```json
{
  "workout.new_exercise": "New Exercise"
}
```

2. **Use in code**:
```typescript
import { useTranslation } from '@tolgee/react';

const { t } = useTranslation();
return <Text>{t('workout.new_exercise')}</Text>;
```

3. **Pull translations from Tolgee**:
```bash
npm run pull-translations
```

### Working with Encrypted Feeds

**Reading feed items**:

```typescript
import { useAppSelector } from '@/store';

// Feed items are automatically decrypted by the feed service
const feedItems = useAppSelector(state => state.feed.items);

// NEVER try to decrypt manually in components
// The encryption service handles this in Redux effects
```

**Publishing feed items**:

```typescript
import { publishSession } from '@/store/feed';

dispatch(publishSession({
  session: completedSession,
}));

// The effect will:
// 1. Serialize to Protocol Buffer
// 2. Sign with RSA private key
// 3. Encrypt with AES key
// 4. Send to server
```

### Database Migrations

**C# (Entity Framework Core)**:

```bash
cd backend/LiftLog.Api
dotnet ef migrations add MigrationName
dotnet ef database update
```

**Python (Alembic)**:

```bash
cd backend-python
uv run alembic revision --autogenerate -m "Migration description"
uv run alembic upgrade head

# Downgrade if needed
uv run alembic downgrade -1
```

### Running Full Stack Locally

**Terminal 1 - Frontend**:
```bash
cd app
npm start
```

**Terminal 2 - Backend (Python recommended)**:
```bash
cd backend-python
docker-compose up -d  # Start PostgreSQL
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

**Terminal 3 - Backend (C# alternative)**:
```bash
cd backend/LiftLog.Api
dotnet run
```

**Access**:
- Frontend: `http://localhost:8081` (or Expo Go app)
- Python API: `http://localhost:8000`
- C# API: `http://localhost:5000`

---

## Git Workflow

### Branching Strategy

```bash
# Feature branches
git checkout -b feature/description

# Bug fixes
git checkout -b fix/description

# Releases
git checkout -b release/v1.2.3
```

### Commit Messages

**Format**: Clear, descriptive, imperative mood

```bash
# ✅ GOOD
git commit -m "Add workout sharing feature"
git commit -m "Fix crash when deleting exercise"
git commit -m "Update encryption to use AES-256"

# ❌ BAD
git commit -m "stuff"
git commit -m "fixed it"
git commit -m "WIP"
```

### Pre-commit Checklist

- [ ] Code compiles and passes all tests
- [ ] Linting and formatting checks pass:
  - Frontend: `npm run lint`
  - C# Backend: `dotnet csharpier .`
  - Python Backend: `uv run ruff format . && uv run ruff check .`
- [ ] TypeScript type check: `npm run typecheck`
- [ ] No sensitive information (API keys, passwords, etc.)
- [ ] Protocol Buffer code regenerated if `.proto` files changed
- [ ] Database migrations created if models changed

### Pull Request Guidelines

1. **PR title**: Clear description of changes
2. **PR description**:
   - What changed and why
   - Related issues (fixes #123)
   - Testing performed
   - Screenshots (for UI changes)
3. **Checks must pass**:
   - All CI/CD workflows (builds, tests, formatting)
   - No merge conflicts
4. **Review**: Wait for code review approval

---

## CI/CD Workflows

**GitHub Actions** (`.github/workflows/`):

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `format.yml` | Push | Check C# formatting (CSharpier) |
| `ui-test.yml` | Push | Frontend + E2E tests |
| `ui-unit-test.yml` | Push | Frontend unit tests |
| `api-test.yml` | Push | Backend API tests |
| `android-build.yml` | Push | Build Android debug APK |
| `ios-build.yml` | Push | Build iOS debug app |
| `android-publish.yml` | Release | Publish to Google Play |
| `ios-publish.yml` | Release | Publish to App Store |
| `web-publish.yml` | Release | Deploy web app |
| `api-publish.yml` | Release | Deploy API |

**All checks must pass before merging PRs.**

---

## Troubleshooting

### Common Issues

**Frontend won't build**:
```bash
# Clear caches
cd app
rm -rf node_modules .expo
npm install
npx expo start -c
```

**Protocol Buffer errors**:
```bash
cd app
npm run proto  # Regenerate from .proto files
```

**Database migration conflicts**:
```bash
# Python
cd backend-python
uv run alembic downgrade -1
uv run alembic upgrade head

# C#
cd backend/LiftLog.Api
dotnet ef database drop
dotnet ef database update
```

**Type errors after updating dependencies**:
```bash
cd app
npm run typecheck -- --force
rm -rf .expo
```

---

## Additional Resources

- **Main README**: `/README.md`
- **Contributing Guide**: `/CONTRIBUTING.md`
- **Feed Encryption**: `/docs/FeedProcess.md`
- **Remote Backup**: `/docs/RemoteBackup.md`
- **Plaintext Export**: `/docs/PlaintextExport.md`
- **Discord**: https://discord.gg/YHhKEnEnFa
- **Demo App**: https://app.liftlog.online

---

## Quick Reference Card

### Essential Commands

```bash
# Frontend
cd app && npm test                           # Run tests
cd app && npm run lint                       # Lint
cd app && npm run typecheck                  # Type check
cd app && npm run proto                      # Generate Protocol Buffers

# Backend (C#)
cd backend/LiftLog.Api && dotnet csharpier . # Format
cd backend/LiftLog.Api && dotnet test        # Test

# Backend (Python)
cd backend-python && uv run ruff format .    # Format
cd backend-python && uv run pytest           # Test
cd backend-python && uv run mypy app         # Type check
```

### File Locations

| What | Where |
|------|-------|
| Redux state | `app/store/<feature>/index.ts` |
| Redux effects | `app/store/<feature>/effects.ts` |
| API services | `app/services/*-api.ts` |
| Components | `app/components/presentation/` |
| Models | `app/models/*-models.ts` |
| Proto schemas | `proto/*.proto` |
| Generated proto | `app/gen/proto.{js,d.ts}` |
| Translations | `app/i18n/*.json` |
| C# Controllers | `backend/LiftLog.Api/Controllers/` |
| Python Routes | `backend-python/app/api/routes/` |

### Don't Forget

- ✅ Run `npm run proto` after changing `.proto` files
- ✅ Run `dotnet csharpier .` before committing C# code
- ✅ Use `@/` imports, not relative paths
- ✅ Co-locate tests with source files (`.spec.ts`)
- ✅ Use Protocol Buffers for all persisted data
- ✅ Follow import restrictions (ESLint enforces)
- ✅ Platform-specific code → `.native.ts` suffix
- ✅ Backend encryption → RSA + AES (see `/docs/FeedProcess.md`)

---

**Last Updated**: 2025-11-23 by AI Assistant
**Status**: Active Development (Backend migration to Python in progress)
