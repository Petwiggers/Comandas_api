# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

**Comandas API** — a FastAPI backend for a restaurant/pastry shop point-of-sale system. It manages orders (comandas), payments (recebimentos), products, employees (funcionários), customers (clientes), and maintains a full audit trail. The codebase is in **Portuguese (PT-BR)**.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (reads src/.env for HOST/PORT/RELOAD)
python src/main.py

# Run production stack (MySQL + API with QUIC/HTTP3 on port 4443)
docker-compose -f src/compose.yml up
```

There is no automated test suite. Manual tests are REST files in `src/testes/` (usable with VS Code REST Client extension).

## Environment Configuration

Copy/create `src/.env` with these variables:

```
HOST=0.0.0.0
PORT=8000
RELOAD=True
DB_SGDB=sqlite          # sqlite | mysql | mssql
DB_NAME=comandas_db.db
DB_HOST=localhost
DB_USER=
DB_PASS=
DB_PORT=3306
SECRET_KEY=<random>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=*
RATE_LIMIT_CRITICAL=5/minute
RATE_LIMIT_RESTRICTIVE=20/minute
RATE_LIMIT_MODERATE=100/minute
RATE_LIMIT_LOW=200/minute
```

`src/settings.py` reads this file and constructs async database URLs (aiosqlite, aiomysql) or a sync URL for SQL Server.

## Architecture

### Layer Structure

```
src/
├── main.py               # App factory: middleware, routers, lifespan
├── settings.py           # Settings from .env; DB URL construction
├── domain/schemas/       # Pydantic request/response models
├── infra/
│   ├── orm/              # SQLAlchemy declarative models
│   ├── database.py       # Async engine + AsyncSession factory
│   ├── security.py       # JWT creation/verification, bcrypt hashing
│   ├── dependencies.py   # FastAPI dependencies (auth, group guards)
│   ├── rate_limit.py     # slowapi limiter instance
│   └── middleware/       # IPAccessMiddleware
├── routers/              # HTTP handlers (one file per resource)
├── services/             # AuditoriaService (audit log helper)
└── enums/                # Payment type enum
```

### Data Model Relationships

- **Funcionário** (employee) creates/manages **Comanda** (order) and processes **Recebimento** (payment)
- **Comanda** ↔ **Produto** via **ComandaProduto** join table (many-to-many)
- **Recebimento** ↔ **Comanda** via **RecebimentoComanda** join table (supports paying multiple orders at once)
- **Auditoria** records every mutating action with employee ID, IP, and user-agent

### Auth & Authorization

- JWT access tokens (15 min) + refresh tokens (7 days) via `HTTPBearer`
- `src/infra/dependencies.py` exports `get_current_user` and per-group guards (`get_grupo_1`, `get_grupo_2`, etc.)
- Groups 1–3 represent permission tiers; endpoints declare which groups are allowed via dependency injection

### Comanda Status

- `0` = open, `1` = closed, `2` = cancelled

### Async Pattern

All routers use `AsyncSession` from SQLAlchemy 2.0. Always `await` DB calls and use `async with session` or dependency-injected sessions. Do not mix sync SQLAlchemy calls.

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/main.py` | App wiring — add new routers here |
| `src/infra/dependencies.py` | Auth dependencies used across all routers |
| `src/infra/orm/` | Source of truth for DB schema |
| `src/domain/schemas/` | Pydantic schemas; keep in sync with ORM models |
| `src/routers/RecebimentoRouter.py` | Most complex router: dashboard, multi-comanda payment, receipt PDF |
| `src/services/AuditoriaService.py` | Call this after every mutating operation |
