# LiftLog API v2 - Python/FastAPI

**Privacy-first fitness tracking backend** with end-to-end encryption, built with FastAPI and SQLModel.

This is a Python rewrite of the original C# ASP.NET Core backend, designed for deployment to Google Play and Apple App Store backends.

## 🏗️ Architecture

### Technology Stack

- **Framework:** FastAPI 0.115+ with async/await
- **Database:** PostgreSQL with asyncpg driver
- **ORM:** SQLModel (combines SQLAlchemy + Pydantic)
- **Migrations:** Alembic
- **Security:** PBKDF2-SHA512 password hashing, end-to-end encryption
- **AI:** OpenAI GPT-4o for workout generation
- **Package Manager:** uv (fast Python package manager)
- **Testing:** pytest with async support

### Project Structure

```
backend-python/
├── app/
│   ├── api/routes/          # API endpoints
│   ├── models/
│   │   ├── database/        # SQLModel database models
│   │   └── schemas/         # Pydantic request/response schemas
│   ├── services/            # Business logic
│   ├── auth/                # Authentication handlers
│   ├── db/                  # Database session management
│   ├── core/                # Configuration and utilities
│   └── main.py              # FastAPI app
├── tests/                   # pytest tests
├── alembic/                 # Database migrations
├── Dockerfile               # Multi-stage Docker build
├── pyproject.toml           # uv dependencies
└── .env.example             # Environment variables template
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

The easiest way to get started:

```bash
# 1. Set your OpenAI API key
export OPENAI_API_KEY=sk-your-key-here

# 2. Start all services
docker-compose up -d

# 3. View logs
docker-compose logs -f api

# 4. Stop services
docker-compose down
```

**Services:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050 (admin@liftlog.com / admin)

### Option 2: Local Development

**Prerequisites:**
- Python 3.12+
- PostgreSQL 14+
- [uv](https://github.com/astral-sh/uv) package manager

**Installation:**

1. **Install uv:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Install dependencies:**

```bash
uv sync
```

3. **Set up environment:**

```bash
cp .env.development .env
# Edit .env with your configuration (especially OPENAI_API_KEY)
```

4. **Start PostgreSQL and create databases:**

```sql
CREATE DATABASE liftlog_user_data;
CREATE DATABASE liftlog_rate_limit;
```

5. **Run migrations:**

```bash
uv run alembic upgrade head
```

6. **Start development server:**

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Interactive Documentation

Once the server is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

### API Endpoints (v2)

**Base URL:** `http://localhost:8000/v2`

#### User Management

- `POST /v2/user/create` - Create new user with auto-generated credentials
- `GET /v2/user/{idOrLookup}` - Get user by ID or lookup string
- `PUT /v2/user` - Update user encrypted data (requires password)
- `POST /v2/user/delete` - Delete user account (requires password)
- `POST /v2/users` - Get multiple users by ID (batch operation)

#### Events

- `PUT /v2/event` - Create or update workout event
- `POST /v2/events` - Get events from followed users

#### Social Features

- `PUT /v2/follow-secret` - Create follow token
- `POST /v2/follow-secret/delete` - Revoke follow token
- `PUT /v2/inbox` - Send encrypted message
- `POST /v2/inbox` - Get and clear inbox messages

#### Sharing

- `POST /v2/shareditem` - Create shareable workout item
- `GET /v2/shareditem/{id}` - Get shared item

#### AI Workout Generation (requires purchase token)

- `POST /v2/ai/workout` - Generate AI workout plan
- `POST /v2/ai/session` - Generate AI workout session
- `WS /ai-chat` - Real-time AI workout chat (WebSocket)

#### Health

- `GET /health` - Health check endpoint

## 🧪 Testing

Run tests with pytest:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_api/test_users.py

# Run with verbose output
uv run pytest -v
```

## 🔒 Security

### Password Hashing

- **Algorithm:** PBKDF2 with SHA512
- **Iterations:** 350,000 (matching C# backend)
- **Key Size:** 64 bytes
- **Comparison:** Constant-time to prevent timing attacks

### End-to-End Encryption

- **User data:** Client-side AES encryption
- **Server storage:** Encrypted payloads + IVs (NOT keys)
- **Inbox messages:** RSA public key encryption with chunking
- **Shared items:** AES key embedded in share URL

### Authentication

- **Purchase Token Auth:** For AI features (Google Play, Apple, RevenueCat, Web)
- **Password Auth:** For basic user operations
- **Rate Limiting:** Per-store limits (Web: 100/day, Mobile: 20/day)

## 🐳 Docker Deployment

### Development with Docker Compose

```bash
# Start all services (PostgreSQL + API + pgAdmin)
docker-compose up -d

# View logs
docker-compose logs -f api

# Rebuild after code changes
docker-compose up -d --build

# Stop services
docker-compose down

# Remove volumes (reset database)
docker-compose down -v
```

### Production Docker Build

```bash
# Build production image
docker build -t liftlog-api:v2 --target base .

# Run with environment variables
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e OPENAI_API_KEY=sk-... \
  liftlog-api:v2
```

## 🗄️ Database Migrations

Create a new migration:

```bash
uv run alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```bash
# Upgrade to latest
uv run alembic upgrade head

# Downgrade one revision
uv run alembic downgrade -1

# Show current revision
uv run alembic current

# Show migration history
uv run alembic history
```

## 📊 Database Schema

### User Data Database

- **users** - User accounts with encrypted data
- **user_events** - Encrypted workout events (max 5KB)
- **user_follow_secrets** - Revocable follow tokens
- **user_inbox_items** - Encrypted messages (chunked)
- **shared_items** - Publicly shareable items (max 20KB)

### Rate Limit Database

- **rate_limit_consumptions** - API rate limit tracking

All tables use snake_case naming convention and UUID primary keys.

## 🌍 Environment Variables

See `.env.example` for full configuration. Key variables:

```env
# Database
DATABASE_URL=postgresql+asyncpg://localhost/liftlog_user_data
RATE_LIMIT_DATABASE_URL=postgresql+asyncpg://localhost/liftlog_rate_limit

# OpenAI
OPENAI_API_KEY=sk-...

# Purchase Verification
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
APPLE_SHARED_SECRET=your-secret
REVENUECAT_API_KEY=your-key

# Rate Limiting
RATE_LIMIT_WEB_PER_DAY=100
RATE_LIMIT_MOBILE_PER_DAY=20
```

## 🔧 Development

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy app
```

### Database Console

```bash
# PostgreSQL
psql -d liftlog_user_data

# Query users
SELECT id, user_lookup, created FROM users;
```

## 📈 Migration from C# Backend

This Python implementation maintains **full compatibility** with the C# backend:

- ✅ Same database schema (snake_case naming)
- ✅ Same password hashing (PBKDF2-SHA512, 350k iterations)
- ✅ Same API contracts (request/response models)
- ✅ Same encryption approach (AES + RSA)
- ✅ Same rate limiting logic
- ✅ v2 API endpoints for clear separation

### Migration Steps

1. Deploy Python API alongside C# API
2. Configure clients to use `/v2` endpoints
3. Gradually migrate traffic
4. Monitor error rates and performance
5. Decommission C# API when complete

## 🤝 Contributing

1. Write tests for new features
2. Follow PEP 8 style guide (enforced by ruff)
3. Use type hints for all functions
4. Update documentation

## 📄 License

See main repository license.

## 🙋 Support

For issues and questions, please use the GitHub issue tracker in the main repository.

---

**Built with ❤️ using FastAPI, SQLModel, and uv**
