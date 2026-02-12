---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-02-07'
inputDocuments:
  - prd.md
  - prd-validation-report.md
  - product-brief-rental-pro-jgokz-2026-02-01.md
  - ux-design-specification.md
  - research/market-posutochnaya-arenda-kz-research-2026-02-03.md
workflowType: 'architecture'
project_name: 'rental-pro-jgokz'
user_name: 'Erda'
date: '2026-02-07'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

74 функциональных требования (FR1-FR74):
- **MVP (62 FR):** Поиск NLP (FR1-FR12), бронирование и оплата (FR13-FR28a), управление квартирами (FR29-FR42), верификация и рейтинги (FR43-FR50), коммуникация (FR51-FR55), администрирование (FR56-FR62)
- **Phase 2 (12 FR):** Корпоративные заказчики (FR63-FR66), агентства (FR67-FR69), RBAC (FR70-FR71), WhatsApp (FR72), NLP v2 (FR73), SEO (FR74)

**Архитектурно значимые FR-кластеры:**

| Кластер | FR | Архитектурная импликация |
|---------|-----|-------------------------|
| NLP Conversational | FR1-FR3, FR8-FR10 | Отдельный NLP-сервис, fallback strategy, state management |
| Real-time Availability | FR5, FR14 | Booking hold (10 мин TTL), race condition prevention |
| Payment Pipeline | FR15-FR17, FR23 | Payment Provider abstraction, Kaspi OCR → PayBox migration path |
| Smart Lock Integration | FR25-FR28a | TTLock API, 4-уровневый fallback, гарантия заселения |
| Calendar Sync | FR32-FR33 | Google Calendar API, bidirectional sync ≤15 мин |
| Multi-role Platform | FR29-FR42, FR56-FR62 | 3 роли MVP + RBAC Phase 2, role-based data access |

**Non-Functional Requirements:**

| Категория | Ключевые NFR | Архитектурное влияние |
|-----------|-------------|---------------------|
| Performance | Bot ≤2 сек, NLP ≤3 сек, 1000 concurrent, p95 ≤3 сек | Async FastAPI, Redis caching, connection pooling |
| Security | Серверы в КЗ, encryption at rest, RBAC | Managed hosting в KZ, pgcrypto, row-level security |
| Scalability | 200→1000 квартир, 3x трафика, multi-city | Horizontal scaling, city as DB partition key |
| Integration | 8 API: Telegram, NLP, TTLock, Calendar, 3× Payment | Circuit breaker, retry budgets, provider abstraction |
| Monitoring | p50/p95/p99 latency, integration failure rates | Structured logging, metrics, alerting |

### Technology Stack Decision

**Backend: FastAPI (Python) + PostgreSQL**

| Компонент | Технология | Обоснование |
|-----------|-----------|-------------|
| API Server | **FastAPI** | Async-native, Pydantic validation, auto OpenAPI, Python NLP ecosystem |
| Database | **PostgreSQL** | ACID (платежи), JSONB (NLP context), row-level security (RBAC), proven at scale |
| Cache / Session | **Redis** | Session Context (TTL 30 мин), booking holds, event queue |
| Bot Framework | **aiogram 3** (Python) | Async, webhook-native, один язык с FastAPI |
| Frontend | **Next.js** (TypeScript) | Landing SSR/SEO + Admin SPA + Mini App host |
| Monorepo | **Turborepo** (frontend) + **uv workspaces** (Python) | Shared types, shared UI, shared bot templates |

**Обоснование Python backend:**
- NLP ecosystem (spaCy, transformers, LangChain) — нативная интеграция без REST overhead
- FastAPI async = отличная производительность для I/O-bound операций (API calls, DB queries)
- Один язык для Bot + API + NLP + Background tasks
- Pydantic models = strict validation + auto-serialization + OpenAPI docs
- SQLAlchemy 2.0 async + Alembic для миграций

### Architectural Concerns (Party Mode)

**1. Payment Provider Abstraction:**

```python
# Абстракция для миграции Kaspi → OCR → PayBox
class PaymentProvider(Protocol):
    async def initiate(self, booking: Booking) -> PaymentIntent: ...
    async def verify(self, intent: PaymentIntent, proof: bytes) -> PaymentResult: ...
    async def refund(self, payment: Payment, amount: Decimal) -> RefundResult: ...
```

MVP: `KaspiManualProvider` (ручная верификация скриншотов)
Sprint 2-3: `KaspiOCRProvider` (Tesseract/EasyOCR → auto-approve при match ±5%)
Phase 2: `PayBoxProvider` (полная автоматизация)
Переключение без изменения бизнес-логики.

**2. NLP как отдельный сервис:**

```
Bot Service (aiogram) → NLP Service (FastAPI) → Intent + Entities
                              ↓ fallback
                    Structured flow (кнопки)
```

NLP Service деплоится независимо — обновление модели ≠ редеплой бота. В MVP может быть отдельным процессом, не отдельным сервером.

**3. Event Bus с первого дня:**

MVP: In-process event bus (Python `asyncio` + Redis pub/sub через `arq`)
Phase 2: Redis Streams или NATS

```python
# MVP: simple event dispatch
await event_bus.emit("booking.created", BookingCreated(booking_id=..., guest_id=...))
# Listeners: notify_host, hold_apartment, create_payment_intent
```

### Scale & Complexity Assessment

| Аспект | Уровень | Детали |
|--------|---------|--------|
| **Overall complexity** | High | 4 клиента, 8 интеграций, NLP, real-time, payments |
| **Primary domain** | Full-stack marketplace | Telegram-native, Python backend, TypeScript frontend |
| **Estimated DB tables** | ~18-22 | users, apartments, bookings, payments, reviews, events, sessions, calendar_sync, lock_codes, notifications, ... |
| **Estimated API endpoints** | ~40-50 | CRUD + search + payments + webhooks + admin |
| **Deployable units** | 3-4 | API (FastAPI), Bot (aiogram), Web (Next.js), NLP (FastAPI) |
| **Background workers** | 3-5 | Payment verification, calendar sync, notifications, cleanup |

### MVP Scope Boundary (Party Mode)

**Влияет на архитектуру MVP (даже если не строим фичу):**

| Будущая фича | Как влияет на MVP schema/code |
|-------------|-------------------------------|
| Multi-city (NFR-SC3) | `city_id` в apartments, bookings. Не hardcode "Астана" |
| RBAC (FR70-71) | `role: enum` в users table. Middleware проверяет роль |
| WhatsApp (FR72) | `MessagePlatform` abstraction в Bot Service |
| Agency hierarchy (FR67-69) | `organization_id` nullable FK в users |

**Explicitly out of MVP architecture:**
- FR63-FR66: Corporate booking — отдельный модуль Phase 2
- FR67-FR69: Agency management — отдельный модуль Phase 2
- FR70-FR71: RBAC UI — Admin SPA Phase 2 (backend role field — MVP)
- FR74: SEO pages — Next.js dynamic routes Phase 2

### Solo-Founder Constraint (Party Mode)

**P0 Architectural Principle: ≤30 мин/день на operations**

| Правило | Реализация |
|---------|-----------|
| **Single-command deploy** | `git push main` → CI/CD → production |
| **Managed services** | Managed PostgreSQL, managed Redis, managed hosting |
| **Auto-recovery** | Health checks + auto-restart + alerting |
| **Zero-config monitoring** | Один дашборд (Sentry free) |
| **Minimal infrastructure** | ≤3 servers/services. Docker Compose для dev, managed для prod |

### Cost Ceiling (Party Mode)

**Infrastructure cost ≤$100/мес на MVP, scaling to ≤$300/мес при 1000 квартирах**

| Компонент | Free tier | Paid ceiling (MVP) |
|-----------|-----------|-------------------|
| Hosting (API + Bot + NLP) | — | ≤$50/мес (VPS в KZ) |
| PostgreSQL managed | Supabase free (500MB) | ≤$25/мес |
| Redis managed | Upstash free (10K cmds/day) | ≤$10/мес |
| Next.js hosting | Vercel free | $0 |
| CDN / Images | Cloudflare free | $0 |
| Monitoring | Sentry free (5K events) | $0 |
| Domain + SSL | — | ≤$15/год |
| **Total** | | **≤$100/мес** |

### Data Retention Policy (Party Mode)

| Данные | Retention | Обоснование |
|--------|-----------|-------------|
| Booking history | 3 года | Налоговая отчётность КЗ |
| Chat history | 1 год | Dispute resolution |
| Payment screenshots | 90 дней | Верификация, потом удалить (PII) |
| Session context (Redis) | 30 мин TTL | UX spec: state-aware NLP |
| Soft-deleted users | 30 дней | FR50: право на удаление |
| Logs | 90 дней | Debugging + compliance |

### API Design Principles (Party Mode)

**Правило: один экран = максимум один API call**

| UX Screen | API Endpoint | Данные |
|-----------|-------------|--------|
| Главная (Card Stack) | `GET /api/home` | 3 секции: instant, popular, nearby |
| Поиск | `GET /api/search` | NLP query + filters → paginated results |
| Карточка full | `GET /api/apartments/{id}` | Full details + reviews + host info |
| Оплата | `POST /api/bookings` → `POST /api/payments/initiate` | Бронь → оплата |
| Хозяин: дайджест | `GET /api/host/digest` | Вчерашняя статистика |

### Image Upload Architecture (Party Mode)

```
Host upload (Mini App)
  → Pre-signed URL (FastAPI → S3-compatible storage)
  → Direct upload to storage (НЕ через API server)
  → Webhook/callback → resize worker (arq)
  → 3 варианта: thumb 400×300, full 750×1000, original
  → CDN URL saved to DB
```

Фото НЕ идут через API server. Direct upload через pre-signed URL.

### Bot ↔ Mini App Data Bridge (Party Mode)

| Переход | Механизм | Data passing |
|---------|----------|-------------|
| Bot → Mini App | `t.me/bot/app?startapp={payload}` | payload ≤64 символов. Сложный контекст → Redis session_id |
| Mini App → Bot | `Telegram.WebApp.sendData(json)` | Max 4096 bytes. Больше → API call + reference ID |
| Mini App auth | `Telegram.WebApp.initData` | HMAC validation на FastAPI |

### Monorepo Structure (Party Mode)

```
zhilye-go/
├── packages/                    # TypeScript (Turborepo)
│   ├── types/                   # @zhilye-go/types — shared TS interfaces
│   ├── ui/                      # @zhilye-go/ui — React components + tokens
│   └── bot-templates/           # @zhilye-go/bot-templates (reference for Python)
├── apps/
│   └── web/                     # Next.js: Landing (SSR) + Admin SPA + Mini App
├── backend/                     # Python (uv workspaces)
│   ├── api/                     # FastAPI main API
│   ├── bot/                     # aiogram 3 Telegram bot
│   ├── nlp/                     # NLP service (FastAPI)
│   ├── workers/                 # Background tasks (arq)
│   └── shared/                  # Shared Python models, utils
├── docker-compose.yml           # Full dev environment
├── Dockerfile.api
├── Dockerfile.bot
└── Dockerfile.web
```

### Dev Environment Constraint (Party Mode)

```bash
git clone ... && docker compose up
# → PostgreSQL, Redis, API, Bot, NLP, Next.js — всё за ≤2 мин
```

### Database Migrations Strategy (Party Mode)

- **Alembic** для PostgreSQL миграций
- **Forward-only** migrations в production (нет downgrade)
- **CI check**: `alembic heads` → fail if multiple heads
- Каждый PR с DB changes = обязательный migration file

### Testing Strategy (Party Mode)

| Уровень | Tool | Coverage target |
|---------|------|:---:|
| Unit (Python) | pytest + pytest-asyncio | ≥80% бизнес-логики |
| Unit (TypeScript) | Vitest | ≥70% компонентов |
| Integration (API) | pytest + httpx TestClient | Все endpoints |
| E2E | Playwright | 6 critical paths (из UX spec) |
| Bot | pytest + aiogram test utilities | NLP flows + payment flows |

**CI блокирует merge если coverage < threshold.**

### Cross-Cutting Concerns

| Concern | Где проявляется | Решение |
|---------|-----------------|---------|
| **Authentication** | Bot (Telegram ID), Mini App (initData HMAC), Admin (JWT), Landing (public) | Unified auth middleware, Telegram-first |
| **i18n** | Bot templates, Mini App, Admin, Landing | `i18next` (frontend), Python i18n (backend) |
| **Logging** | Все сервисы | Structured JSON logging, correlation ID per request |
| **Error handling** | Bot (friendly), API (structured), Admin (toast) | Centralized error handler + per-platform formatting |
| **Rate limiting** | API endpoints | FastAPI middleware + Redis counters (NFR-S7, S8) |
| **Data validation** | API input, bot messages, admin forms | Pydantic (backend), Zod (frontend) |

### Technical Constraints & Dependencies

| Constraint | Source | Impact |
|-----------|--------|--------|
| Серверы в Казахстане | Закон РК о ПД | Hosting: KZ datacenter (PS.kz, Selectel KZ) |
| Telegram WebView limits | Telegram Mini App | HashRouter, viewportStableHeight, no zoom |
| Kaspi ручная верификация → OCR Sprint 2-3 | Business priority | Payment automation = architectural priority |
| Solo founder | Resource constraint | Max automation, managed services, simple ops |
| Cost ceiling ≤$100/мес | Budget constraint | Free tiers, VPS, no enterprise services |
| `startapp` payload ≤64 chars | Telegram limit | Redis session for complex context passing |

## Starter Template Evaluation

### Primary Technology Domain

Full-stack marketplace: Telegram-native bot + Web Admin SPA + Mini App. Python backend + TypeScript frontend.

### Starter Options Considered

| Вариант | Описание | Вердикт |
|---------|----------|---------|
| **full-stack-fastapi-template (tiangolo)** | FastAPI + React + Vite + SQLModel + Docker + CI/CD | ✅ Выбран |
| Custom monorepo (Next.js + FastAPI + Turborepo) | Сборка с нуля по Step 2 архитектуре | ❌ Overhead для MVP |
| cookiecutter-fastapi | Только backend, без frontend | ❌ Неполный |

### Selected Starter: full-stack-fastapi-template

**Rationale:**
- Production-ready из коробки: auth, CRUD, Docker, Traefik, CI/CD, E2E тесты
- Активно поддерживается (tiangolo — автор FastAPI)
- SQLModel = Pydantic + SQLAlchemy — единая модель для API и DB
- Vite + React + TanStack Router покрывает Admin SPA + Telegram Mini App
- Экономит ~неделю настройки инфраструктуры

**Initialization:** Проект уже инициализирован через copier из этого шаблона.

### Architectural Decisions Provided by Starter

**Language & Runtime:**
- Python 3.10+ (backend), TypeScript 5.9 strict (frontend)
- Package managers: uv (Python), bun (Node.js)

**ORM & Database:**
- SQLModel (Pydantic + SQLAlchemy hybrid)
- PostgreSQL 18, Alembic migrations
- UUID primary keys, created_at timestamps

**Frontend Stack:**
- React 19 + Vite 7.3 + TanStack Router (file-based routing)
- TanStack React Query (data fetching + caching)
- Radix UI + Tailwind CSS (shadcn/ui pattern)
- Zod validation, React Hook Form
- Auto-generated API client (openapi-ts SDK)

**Auth & Security:**
- JWT + OAuth2, Argon2/Bcrypt password hashing
- Timing attack prevention, CORS configuration

**Code Quality:**
- Biome (frontend linting/formatting), Ruff (Python linting/formatting)
- pre-commit hooks, 90%+ backend coverage requirement

**Testing:**
- pytest + coverage (backend), Playwright (E2E)
- 4-shard parallel E2E execution

**DevOps:**
- Docker Compose (dev) + Traefik (production reverse proxy)
- Let's Encrypt auto-SSL
- GitHub Actions: backend tests, Playwright, staging/production deploy
- Multi-stage Dockerfiles (uv-based Python, bun-based frontend → nginx)

### Архитектурные изменения для rental-pro (Party Mode consensus)

| # | Изменение | Приоритет | Обоснование |
|---|-----------|-----------|-------------|
| 1 | Async DB (asyncpg + AsyncSession) | P0 | 8 интеграций = I/O bound, async-native FastAPI |
| 2 | Redis в compose.yml | P0 | Sessions, booking holds (10 мин TTL), cache, event bus |
| 3 | `backend/bot/` — aiogram 3 workspace | P0 | Core product — Telegram bot |
| 4 | `backend/workers/` — arq background tasks | P0 | Payment verification, calendar sync, notifications |
| 5 | NLP как модуль внутри API (не отдельный сервис) | P0 | Solo founder: меньше сервисов = меньше ops. Разделить при bottleneck |
| 6 | Vitest для frontend unit-тестов | P1 | После MVP стабилизации |
| 7 | Next.js landing (SEO) | Phase 2 | FR74 = Phase 2, отдельное приложение |

### Отклонения от Step 2 Architecture

| Step 2 решение | Новое решение | Причина |
|----------------|---------------|---------|
| Next.js (SSR/SEO + Admin + Mini App) | Vite + React (Admin + Mini App) | SSR не нужен для MVP; SEO = Phase 2 |
| SQLAlchemy 2.0 async | SQLModel + async migration | SQLModel уже настроен; поддерживает async через AsyncSession |
| NLP — отдельный FastAPI сервис | NLP — модуль внутри main API | Solo founder constraint: ≤30 мин/день ops |
| Turborepo (frontend monorepo) | bun workspaces | Одно frontend приложение, Turborepo избыточен |
| 3-4 deployable units | 3 units: API+NLP, Bot, Web | NLP внутри API = минус один сервис |

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Async DB migration (asyncpg + AsyncSession)
- Unified auth strategy (Telegram + JWT)
- Shared code structure (backend/shared/)
- Bot ↔ API communication (direct DB via shared CRUD)

**Important Decisions (Shape Architecture):**
- Redis usage patterns (sessions, holds, cache)
- Frontend dual-layout (Admin + Mini App)
- Event/job dispatch via arq
- Image upload pipeline (R2 + Pillow)

**Deferred Decisions (Post-MVP):**
- Redis Streams fan-out (Phase 2)
- Next.js landing SSR/SEO (Phase 2)
- Full RBAC UI (Phase 2)
- WAL archiving / managed PostgreSQL (at scale)

### Data Architecture

**Async Database Layer:**
- Driver: `asyncpg` 0.31.0
- Session: `sqlmodel.ext.asyncio.session.AsyncSession`
- Connection string: `postgresql+asyncpg://...`
- Connection pool: `pool_size=20, max_overflow=10`

**Redis Patterns (Redis 8):**

| Назначение | Key pattern | TTL |
|-----------|-------------|-----|
| NLP session context | `session:{telegram_id}` → JSON | 30 мин |
| Booking hold | `hold:{apartment_id}:{date}` → booking_id | 10 мин |
| Rate limiting | `ratelimit:{ip}:{endpoint}` → counter | 1 мин |
| Cache (apartment cards) | `cache:apartment:{id}` → JSON | 15 мин |
| Job queue | arq (Redis-backed) | — |

**Multi-tenancy:**
- `city_id` как FK в apartments, bookings (не partition key на MVP)
- Индексы: `(city_id, ...)` на основных запросах
- Не hardcode "Астана" — всё через city_id

**Soft Delete:**
- `deleted_at: datetime | None` в users, apartments
- Запросы по умолчанию: `WHERE deleted_at IS NULL`

**Shared Code Structure (Party Mode):**

```
backend/
├── app/           # FastAPI API (routes → shared crud)
├── bot/           # aiogram 3 (handlers → shared crud)
├── workers/       # arq tasks (→ shared crud)
└── shared/        # Shared models, crud, db
    ├── models.py
    ├── crud/
    │   ├── bookings.py
    │   ├── payments.py
    │   └── apartments.py
    └── db.py       # async engine + session factory
```

Рефакторинг `app/models.py` → `shared/models.py` при добавлении бота, не заранее.

### Authentication & Security

**Unified Auth Strategy:**

| Клиент | Auth метод | Flow |
|--------|-----------|------|
| Telegram Bot | Telegram User ID | `message.from_user.id` → DB lookup |
| Mini App | `initData` HMAC | WebApp.initData → HMAC validation → JWT |
| Admin SPA | Email + Password | OAuth2 flow → JWT (уже в шаблоне) |
| Landing | Public | Phase 2, без авторизации |

Mini App после HMAC validation получает тот же JWT, что и Admin SPA. Один middleware, два пути получения токена.

**Role Model:**
- `is_host: bool` flag (не enum) — пользователь может быть и гостем, и хостом
- `is_superuser: bool` — admin (уже в шаблоне)
- Flow "стать хостом": верификация → `is_host = True`
- Phase 2: полный RBAC (FR70-71)

**Row-Level Security:**
- CRUD layer filters (не PostgreSQL RLS на MVP)
- Хост видит свои квартиры/бронирования, гость — свои бронирования, admin — всё

**API Security:**
- Rate limiting: FastAPI middleware + Redis counters
- Лимиты: Guest 30 req/мин, Host 60 req/мин, Admin 120 req/мин
- PII encryption: `pgcrypto` (телефон, паспорт)
- HTTPS only (Traefik + Let's Encrypt)

### API & Communication Patterns

**API Design:**
- REST, `/api/v1/` prefix
- Правило: один экран = один API call
- OpenAPI auto-docs → auto-generated TypeScript SDK (openapi-ts)

**Bot ↔ API Communication:**
- Direct DB access через shared CRUD (не HTTP)
- Bot и API в одном uv workspace, shared models
- HTTP API — для внешних клиентов (Mini App, Admin)

**Event/Job Dispatch (MVP):**

```python
await arq_pool.enqueue_job("on_booking_created", booking_id=...)
# Worker: notify_host, hold_apartment, create_payment_intent
```

arq job queue (не Pub/Sub). Простой, reliable, retry из коробки. Redis Streams — Phase 2 при fan-out.

**Error Handling:**

| Контекст | Формат |
|----------|--------|
| API → Mini App/Admin | `{"detail": "...", "code": "BOOKING_CONFLICT"}` |
| Bot → Guest | Человекочитаемое сообщение RU/KZ |
| Bot → Host | Push notification через Telegram |
| Internal | Structured JSON logging + Sentry, correlation_id |

**Webhook Handling:**
- TTLock: `/api/v1/webhooks/ttlock`
- PayBox: `/api/v1/webhooks/paybox` (Phase 2)
- Telegram: `/bot/webhook` (aiogram native)
- Все: signature validation, idempotency key, async processing через arq

### Frontend Architecture

**Dual-Layout Strategy (один Vite app):**

| Layout | Route prefix | Auth | Особенности |
|--------|-------------|------|-------------|
| Admin SPA | `/_layout/` | Email+Password JWT | Sidebar, таблицы, формы (уже в шаблоне) |
| Mini App | `/_miniapp/` | Telegram initData JWT | Полноэкранный, touch-first, HashRouter |

Shared: UI компоненты, API client, hooks. Разные: layout, navigation, auth flow.

**Telegram Mini App Integration:**
- SDK: `@telegram-apps/sdk` 3.x
- Auth: `WebApp.initData` → POST `/api/v1/auth/telegram` → JWT
- Deep linking: `t.me/bot/app?startapp={session_id}` → Redis lookup
- Viewport: `viewportStableHeight`, safe area insets

**State Management:**
- TanStack React Query — server state (уже есть)
- React Context — UI state (theme, sidebar)
- Нет Redux/Zustand — достаточно Query + Context

**Booking Flow State (Mini App):**
- Multi-step: Поиск → Карточка → Даты → Оплата → Подтверждение
- URL params как source of truth (`/miniapp/book/:apartmentId?checkin=...&checkout=...`)
- Booking hold: `POST /api/v1/bookings/hold` → 10 мин TTL

### Infrastructure & Deployment

**Production Hosting (KZ):**

| Компонент | Решение | Стоимость |
|-----------|---------|-----------|
| VPS (API + Bot + Workers + DB + Redis) | KZ datacenter (PS.kz / Selectel KZ), 4 vCPU / 8GB RAM | ~$40/мес |
| PostgreSQL | Docker на KZ VPS (compliance с первого дня) | Включено |
| Redis | Docker на KZ VPS (TTL-only data) | Включено |
| Frontend | Vercel free tier или Cloudflare Pages | $0 |
| CDN / Images | Cloudflare R2 (S3-compatible, 10GB free) | $0 |
| SSL | Let's Encrypt через Traefik | $0 |
| Monitoring | Sentry free tier (5K events/мес) | $0 |
| **Итого MVP** | | **~$40-55/мес** |

**Deployment Pipeline:**

```
git push main → GitHub Actions CI (тесты, lint) → SSH deploy to KZ VPS
→ docker compose pull && docker compose up -d → Health check → Sentry release
```

**Docker Compose Production:**

| Сервис | Container | Порты |
|--------|-----------|-------|
| traefik | Reverse proxy + SSL | 80, 443 |
| api | FastAPI (API + NLP module) | 8000 (internal) |
| bot | aiogram 3 (webhook) | — (from Traefik) |
| workers | arq worker | — (background) |
| db | PostgreSQL 18 | 5432 (internal) |
| redis | Redis 8 | 6379 (internal) |
| frontend | nginx (Vite build) | 80 (internal) |

**Backup Strategy:**
- PostgreSQL: `pg_dump` cron daily → Cloudflare R2 (retain 7 days)
- Redis: не бэкапим (TTL-only, reconstructable)
- Images: Cloudflare R2 (replicated by design)

**Monitoring & Alerting:**
- Sentry free tier — errors + performance
- Structured JSON logging → stdout → Docker logs
- Health checks: `/api/v1/utils/health-check/` + Redis PING + DB connection
- Alerting: Sentry → Telegram notification (боту самому себе)

**Image Upload Pipeline (Party Mode):**

```
Host upload (Mini App) → Pre-signed URL (API → R2)
  → Direct upload to R2 (не через API server)
  → arq worker → Pillow resize (thumb 400×300, full 750×1000, original)
  → CDN URL saved to DB
```

### Testing Strategy (Party Mode additions)

| Уровень | Tool | Target |
|---------|------|--------|
| Unit (Python) | pytest + pytest-asyncio | ≥80% shared CRUD |
| Unit (TypeScript) | Vitest (P1, после MVP) | ≥70% компонентов |
| Integration (API) | pytest + httpx TestClient | Все endpoints |
| E2E | Playwright (4 shards) | 6 critical paths |
| Bot | aiogram.testing | NLP + payment flows |
| Redis mock | fakeredis | Unit-тесты с Redis |

### Decision Impact Analysis

**Implementation Sequence:**
1. Async DB migration (asyncpg + AsyncSession) — фундамент
2. Redis в compose.yml — sessions, holds
3. Shared models/crud extraction — при добавлении бота
4. Telegram auth endpoint — Mini App MVP
5. Bot workspace (aiogram 3) — core product
6. arq workers — payment verification, calendar sync
7. Mini App layout — frontend dual-layout
8. Image upload pipeline — host onboarding

**Cross-Component Dependencies:**
- Bot + API + Workers → shared/ (models, crud, db)
- Mini App auth → API auth endpoint → Redis sessions
- Booking hold → Redis TTL → arq cleanup worker
- Image upload → R2 pre-signed URL → arq resize → DB update

## Implementation Patterns & Consistency Rules

### Naming Patterns

**Database (SQLModel):**

| Элемент | Convention | Пример |
|---------|-----------|--------|
| Таблицы | snake_case, **plural** | `users`, `apartments`, `bookings` |
| Колонки | snake_case | `check_in_date`, `is_host`, `created_at` |
| FK | `{entity}_id` | `owner_id`, `apartment_id`, `city_id` |
| Индексы | `ix_{table}_{columns}` | `ix_apartments_city_id` |
| Enum types | PascalCase | `BookingStatus`, `PaymentMethod` |

**API (FastAPI):**

| Элемент | Convention | Пример |
|---------|-----------|--------|
| Endpoints | plural, kebab-case | `/api/v1/apartments`, `/api/v1/booking-holds` |
| Path params | snake_case | `/apartments/{apartment_id}` |
| Query params | snake_case | `?city_id=1&check_in=2026-03-01` |
| JSON fields | snake_case | `{"check_in_date": "...", "total_price": 15000}` |
| Response model | PascalCase | `ApartmentPublic`, `BookingCreate` |

**Python Code:**

| Элемент | Convention | Пример |
|---------|-----------|--------|
| Modules | snake_case | `booking_service.py`, `payment_provider.py` |
| Classes | PascalCase | `BookingService`, `KaspiManualProvider` |
| Functions | snake_case | `create_booking()`, `verify_payment()` |
| Constants | UPPER_SNAKE | `MAX_BOOKING_HOLD_SECONDS = 600` |
| Private | `_prefix` | `_validate_dates()` |

**TypeScript/React:**

| Элемент | Convention | Пример |
|---------|-----------|--------|
| Components | PascalCase file + export | `ApartmentCard.tsx`, `BookingFlow.tsx` |
| Hooks | camelCase, `use` prefix | `useBooking.ts`, `useTelegramAuth.ts` |
| Utils | camelCase | `formatPrice.ts`, `dateUtils.ts` |
| Types/Interfaces | PascalCase | `Apartment`, `BookingStatus` |
| CSS classes | Tailwind utility | `className="flex gap-2 p-4"` |

### Structure Patterns

**Backend Module Organization:**

```
backend/shared/crud/bookings.py     # CRUD операции (бизнес-логика)
backend/app/api/routes/bookings.py  # API routes (тонкая обёртка)
backend/app/api/schemas/bookings.py # API schemas (Create/Public/Update)
backend/bot/handlers/booking.py     # Bot handlers (тонкая обёртка)
backend/workers/tasks/payment.py    # Worker tasks (тонкая обёртка)
```

Правило: **бизнес-логика живёт в `shared/crud/`**, остальные слои — тонкие обёртки.

**Frontend Organization (by feature):**

```
src/routes/_miniapp/book/         # Booking flow pages
src/components/Booking/           # Booking UI components
src/components/Apartment/         # Apartment UI components
src/hooks/useBooking.ts           # Booking-specific hook
```

**Тесты:**
- Backend: `backend/tests/` (mirror структуру `app/`, `shared/`)
- Frontend: `frontend/tests/` (Playwright E2E)

### Format Patterns

**API Responses:**

```python
# Успех — прямой объект (FastAPI convention)
{"id": "uuid", "title": "...", "check_in_date": "2026-03-01"}

# Список — с пагинацией
{"data": [...], "count": 42}

# Ошибка — structured
{"detail": "Квартира занята на эти даты", "code": "BOOKING_CONFLICT"}
```

**Даты:** ISO 8601 строки в JSON (`"2026-03-01T14:00:00+06:00"`), timezone = Asia/Almaty

**Деньги:** `int` в тенге (без копеек). `15000` = 15 000 ₸. Форматирование — на фронте.

**Webhooks:** `/webhooks/{provider}` (без `/api/v1/` — внешние интеграции не версионируются)

### Communication Patterns

**arq Job Naming:**

```python
# Event-driven: "on_{entity}_{action}"
"on_booking_created", "on_payment_received", "on_calendar_sync_needed"

# Direct tasks: "{action}_{entity}"
"send_notification", "resize_image", "cleanup_expired_holds"
```

**arq Job Payload:** всегда ID, не объект:

```python
# ✅ Правильно
await pool.enqueue_job("on_booking_created", booking_id=uuid)

# ❌ Неправильно — stale data risk
await pool.enqueue_job("on_booking_created", booking=booking_dict)
```

**Logging:**

```python
logger.info("booking.created", extra={
    "booking_id": str(booking.id),
    "apartment_id": str(booking.apartment_id),
    "guest_id": str(booking.guest_id),
})
```

Levels: `DEBUG` (dev only), `INFO` (business events), `WARNING` (recoverable), `ERROR` (needs attention).

### Process Patterns

**Error Handling Backend:**

```python
# Custom exceptions в shared/exceptions.py
class BookingConflictError(AppError):
    code = "BOOKING_CONFLICT"
    status_code = 409

# FastAPI exception handler → structured JSON response
# Sentry captures ERROR level automatically
```

**Error Handling Frontend:**
- React Query `onError` → toast (sonner)
- 401/403 → auto-logout (уже в шаблоне)
- Network error → "Проверьте подключение к интернету"

**Loading States (Mini App):**
- Skeleton UI (Radix Skeleton) для initial load
- Inline spinner для actions (кнопка "Забронировать")
- Никогда fullscreen spinner — UX anti-pattern

### Dependency Injection Patterns (Party Mode)

**API (FastAPI):**

```python
SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]
CurrentUser = Annotated[User, Depends(get_current_user)]
```

**Bot / Workers (не FastAPI):**

```python
async with get_session() as session:
    booking = await create_booking(session, ...)
```

### Schema Layer Convention (Party Mode)

```python
# shared/models.py — DB models (SQLModel, table=True)
class Apartment(SQLModel, table=True):
    id: uuid.UUID
    title: str
    ...

# app/api/schemas/apartments.py — API schemas
class ApartmentCreate(SQLModel):    # input
class ApartmentPublic(SQLModel):    # output
class ApartmentUpdate(SQLModel):    # partial update
```

Naming: `{Entity}Create`, `{Entity}Public`, `{Entity}Update`. Никогда не возвращать DB model напрямую в API response.

### Import Convention (Party Mode)

```python
# Абсолютные imports от workspace root
from shared.models import Apartment, Booking
from shared.crud.bookings import create_booking
from shared.db import get_session
```

### Environment Variables Convention (Party Mode)

Pattern: `{SERVICE}_{PARAM}`, все в `.env` и `Settings` class:

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_SECRET=...
REDIS_URL=redis://localhost:6379
TTLOCK_CLIENT_ID=...
TTLOCK_CLIENT_SECRET=...
R2_ACCOUNT_ID=...
R2_ACCESS_KEY=...
R2_SECRET_KEY=...
R2_BUCKET_NAME=...
```

### Test Fixtures Convention (Party Mode)

```python
@pytest.fixture
def guest_user()         # пользователь-гость
def host_user()          # пользователь-хост
def sample_apartment()   # тестовая квартира
def active_booking()     # активное бронирование
def mock_redis()         # fakeredis instance
```

Naming: `{adjective}_{entity}`. Файлы тестов зеркалят структуру `app/` и `shared/`.

### Enforcement Guidelines

**Все AI-агенты ОБЯЗАНЫ:**
1. Следовать naming conventions из таблиц выше
2. Размещать бизнес-логику в `shared/crud/`, не в routes/handlers
3. Использовать snake_case для API JSON fields
4. Передавать в arq jobs только ID, не объекты
5. Писать structured logging с context
6. Использовать `{Entity}Create/Public/Update` для API schemas
7. Не создавать новые файлы без необходимости — расширять существующие

**Enforcement:** Ruff (Python) + Biome (TS) ловят naming violations. PR review ловит structural violations.

## Project Structure & Boundaries

### Complete Project Directory Structure

```
rental-pro-jgokz/
├── .env                            # Environment variables (all services)
├── .env.example                    # Template for .env
├── .gitignore
├── .pre-commit-config.yaml         # Ruff + Biome + pre-commit hooks
├── compose.yml                     # Production Docker Compose
├── compose.override.yml            # Local dev overrides
├── compose.traefik.yml             # Traefik production config
├── pyproject.toml                  # uv workspace root
├── package.json                    # bun workspace root
├── bun.lock
├── uv.lock
│
├── .github/
│   └── workflows/
│       ├── test-backend.yml        # pytest + coverage
│       ├── playwright.yml          # E2E tests (4 shards)
│       ├── deploy-staging.yml      # git push → staging
│       ├── deploy-production.yml   # release → production
│       ├── pre-commit.yml
│       └── test-docker-compose.yml
│
├── scripts/
│   ├── generate-client.sh          # OpenAPI → TypeScript SDK
│   ├── test.sh                     # Docker-based test runner
│   ├── test-local.sh
│   └── backup-db.sh                # pg_dump → R2 (production)
│
├── backend/
│   ├── pyproject.toml              # uv workspace: packages = ["shared", "app", "bot", "workers"]
│   ├── alembic.ini
│   ├── Dockerfile                  # Multi-stage (API)
│   ├── Dockerfile.bot              # Bot container
│   ├── Dockerfile.workers          # Workers container
│   │
│   ├── shared/                     # ← НА УРОВНЕ backend/ (Party Mode fix)
│   │   ├── __init__.py
│   │   ├── models.py               # SQLModel DB models (table=True)
│   │   ├── enums.py                # BookingStatus, PaymentMethod, etc.
│   │   ├── exceptions.py           # AppError, BookingConflictError, etc.
│   │   ├── db.py                   # Async engine, session factory
│   │   ├── redis.py                # Redis connection pool
│   │   ├── crud/
│   │   │   ├── __init__.py
│   │   │   ├── users.py
│   │   │   ├── apartments.py
│   │   │   ├── bookings.py
│   │   │   ├── payments.py
│   │   │   ├── reviews.py
│   │   │   └── cities.py
│   │   ├── services/               # Complex multi-CRUD orchestration
│   │   │   ├── __init__.py
│   │   │   ├── booking_service.py  # Hold + confirm + notify
│   │   │   └── payment_service.py  # Provider abstraction
│   │   └── integrations/           # External API clients (Party Mode fix)
│   │       ├── __init__.py
│   │       ├── ttlock.py           # TTLock API client
│   │       ├── calendar.py         # Google Calendar sync
│   │       ├── kaspi.py            # Kaspi manual verification
│   │       └── r2.py               # Cloudflare R2 (pre-signed URLs)
│   │
│   ├── app/                        # FastAPI API Service
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app (Sentry, CORS, routers)
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Settings (Pydantic BaseSettings)
│   │   │   └── security.py         # JWT, password hashing
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── main.py             # API router aggregation
│   │   │   ├── deps.py             # SessionDep, RedisDep, CurrentUser
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── login.py        # OAuth2 + Telegram auth
│   │   │   │   ├── users.py        # User CRUD
│   │   │   │   ├── apartments.py   # FR29-FR42: Apartment CRUD
│   │   │   │   ├── bookings.py     # FR13-FR28: Booking + holds
│   │   │   │   ├── payments.py     # FR15-FR17: Payment initiation
│   │   │   │   ├── reviews.py      # FR43-FR50: Reviews + ratings
│   │   │   │   ├── search.py       # FR1-FR12: NLP search
│   │   │   │   ├── host.py         # Host dashboard, digest
│   │   │   │   ├── admin.py        # FR56-FR62: Admin endpoints
│   │   │   │   ├── images.py       # Pre-signed URL generation
│   │   │   │   └── utils.py        # Health checks
│   │   │   └── schemas/
│   │   │       ├── __init__.py
│   │   │       ├── apartments.py   # ApartmentCreate/Public/Update
│   │   │       ├── bookings.py     # BookingCreate/Public/Update
│   │   │       ├── payments.py     # PaymentIntent/Result
│   │   │       ├── search.py       # SearchQuery/SearchResult
│   │   │       └── reviews.py      # ReviewCreate/Public
│   │   ├── nlp/                    # NLP Module (in-process)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py           # Intent extraction
│   │   │   ├── entities.py         # Entity recognition
│   │   │   └── fallback.py         # Structured flow fallback
│   │   ├── webhooks/
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # /webhooks/ routes (no versioning)
│   │   │   └── ttlock.py           # TTLock callback handler
│   │   ├── alembic/
│   │   │   ├── versions/           # Migration files
│   │   │   ├── env.py
│   │   │   └── script.py.mako
│   │   ├── email-templates/
│   │   │   ├── src/                # MJML templates
│   │   │   └── build/              # HTML output
│   │   ├── initial_data.py
│   │   └── backend_pre_start.py
│   │
│   ├── bot/                        # Telegram Bot Service (aiogram 3)
│   │   ├── __init__.py
│   │   ├── main.py                 # Bot entry point, webhook setup
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── start.py            # /start, onboarding
│   │   │   ├── search.py           # NLP search conversation
│   │   │   ├── booking.py          # Booking flow
│   │   │   ├── payment.py          # Payment instructions + screenshot
│   │   │   ├── host.py             # Host notifications + management
│   │   │   └── common.py           # Help, cancel, fallback
│   │   ├── keyboards/
│   │   │   ├── __init__.py
│   │   │   ├── inline.py
│   │   │   └── reply.py
│   │   ├── middlewares/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Telegram user → DB user
│   │   │   └── throttle.py         # Rate limiting
│   │   ├── filters/
│   │   │   └── role.py             # IsHost, IsAdmin filters
│   │   ├── templates/
│   │   │   └── messages.py         # All message strings (RU, MVP only)
│   │   └── utils.py
│   │
│   ├── workers/                    # Background Workers (arq)
│   │   ├── __init__.py
│   │   ├── main.py                 # arq WorkerSettings
│   │   └── tasks/
│   │       ├── __init__.py
│   │       ├── notifications.py    # send_notification, notify_host
│   │       ├── payments.py         # on_payment_received, verify
│   │       ├── calendar_sync.py    # Google Calendar bidirectional
│   │       ├── images.py           # resize_image (Pillow)
│   │       └── cleanup.py          # cleanup_expired_holds
│   │
│   ├── tests/
│   │   ├── conftest.py             # Global: db session, redis, users
│   │   ├── shared/
│   │   │   ├── conftest.py         # Shared-specific fixtures
│   │   │   ├── crud/
│   │   │   │   ├── test_bookings.py
│   │   │   │   ├── test_apartments.py
│   │   │   │   ├── test_payments.py
│   │   │   │   └── __init__.py
│   │   │   ├── services/
│   │   │   │   ├── test_booking_service.py
│   │   │   │   ├── test_payment_service.py
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   ├── api/
│   │   │   ├── conftest.py         # API: TestClient, auth headers
│   │   │   ├── routes/
│   │   │   │   ├── test_login.py
│   │   │   │   ├── test_apartments.py
│   │   │   │   ├── test_bookings.py
│   │   │   │   ├── test_payments.py
│   │   │   │   ├── test_search.py
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   ├── bot/
│   │   │   ├── conftest.py         # Bot: mock dispatcher
│   │   │   ├── test_search_handler.py
│   │   │   ├── test_booking_handler.py
│   │   │   └── __init__.py
│   │   ├── nlp/
│   │   │   ├── test_engine.py
│   │   │   └── __init__.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── user.py
│   │       ├── apartment.py
│   │       └── booking.py
│   │
│   └── scripts/
│       ├── prestart.sh
│       ├── tests-start.sh
│       ├── lint.sh
│       └── format.sh
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── biome.json
│   ├── playwright.config.ts
│   ├── openapi-ts.config.ts
│   ├── components.json             # shadcn/ui config
│   ├── nginx.conf
│   ├── Dockerfile
│   │
│   ├── src/
│   │   ├── main.tsx
│   │   ├── index.css
│   │   ├── routeTree.gen.ts        # Generated
│   │   ├── client/                 # Generated OpenAPI SDK
│   │   │
│   │   ├── routes/
│   │   │   ├── __root.tsx
│   │   │   ├── login.tsx
│   │   │   ├── signup.tsx
│   │   │   ├── _layout.tsx         # Admin SPA layout (sidebar)
│   │   │   ├── _layout/
│   │   │   │   ├── index.tsx       # Admin dashboard
│   │   │   │   ├── apartments.tsx  # Apartment management
│   │   │   │   ├── bookings.tsx    # Booking management
│   │   │   │   ├── reviews.tsx     # Reviews moderation
│   │   │   │   ├── settings.tsx    # User settings
│   │   │   │   └── admin.tsx       # Admin panel
│   │   │   ├── _miniapp.tsx        # Mini App layout (fullscreen, Telegram SDK)
│   │   │   └── _miniapp/
│   │   │       ├── index.tsx       # Home (card stack)
│   │   │       ├── search.tsx      # Search results
│   │   │       ├── apartment.$id.tsx  # Apartment detail
│   │   │       ├── book.$id.tsx    # Booking flow
│   │   │       ├── my-bookings.tsx # Guest bookings
│   │   │       └── profile.tsx     # Guest profile
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                 # Radix UI + Tailwind (shadcn/ui)
│   │   │   ├── Common/             # Logo, Footer, ErrorComponent
│   │   │   ├── Apartment/          # ApartmentCard, ApartmentGallery
│   │   │   ├── Booking/            # BookingForm, BookingCard, PaymentStep
│   │   │   ├── Search/             # SearchBar, FilterPanel, ResultCard
│   │   │   ├── Review/             # ReviewCard, ReviewForm, StarRating
│   │   │   ├── Host/               # HostDashboard, ApartmentEditor
│   │   │   ├── Sidebar/            # Admin sidebar
│   │   │   ├── Telegram/           # TelegramProvider, MiniAppLayout
│   │   │   └── theme-provider.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useTelegramAuth.ts
│   │   │   ├── useBooking.ts
│   │   │   ├── useSearch.ts
│   │   │   ├── useMobile.ts
│   │   │   └── useCustomToast.ts
│   │   │
│   │   ├── lib/
│   │   │   ├── utils.ts            # cn() utility
│   │   │   ├── telegram.ts         # Telegram WebApp SDK wrapper
│   │   │   └── format.ts           # formatPrice, formatDate, formatDateRange (KZ locale)
│   │   │
│   │   └── utils.ts
│   │
│   └── tests/                      # Playwright E2E
│       ├── config.ts
│       ├── auth.setup.ts
│       ├── miniapp/
│       │   ├── search.spec.ts
│       │   ├── booking.spec.ts
│       │   └── payment.spec.ts
│       ├── admin/
│       │   ├── apartments.spec.ts
│       │   ├── bookings.spec.ts
│       │   └── admin.spec.ts
│       └── utils/
│
└── .vscode/
    ├── launch.json
    ├── extensions.json
    └── settings.json
```

### Architectural Boundaries

**Request Flow:**

```
External clients (Mini App, Admin SPA)
  → Traefik (SSL termination)
    → /api/v1/*     → FastAPI API routes → shared/crud → PostgreSQL
    → /webhooks/*   → Webhook handlers → arq jobs
    → /bot/webhook  → aiogram webhook (Telegram)
    → /*            → nginx (frontend static)
```

**Dependency Graph (Party Mode fix):**

```
app/  ──→ shared/  ←── bot/
              ↑
          workers/
```

`shared/` не зависит ни от `app/`, ни от `bot/`, ни от `workers/`. Все зависят от `shared/`.

**Data Access Boundary:**
- Routes/Handlers → `shared/crud/` (single CRUD) или `shared/services/` (multi-CRUD orchestration) → SQLModel → PostgreSQL
- Никогда: Routes → DB напрямую

### Requirements to Structure Mapping

| FR Cluster | Backend | Frontend |
|-----------|---------|----------|
| FR1-FR12 NLP Search | `app/nlp/`, `app/api/routes/search.py`, `shared/crud/apartments.py` | `_miniapp/search.tsx`, `components/Search/` |
| FR13-FR28 Booking + Payment | `app/api/routes/bookings.py`, `shared/services/booking_service.py`, `shared/services/payment_service.py` | `_miniapp/book.$id.tsx`, `components/Booking/` |
| FR25-FR28a Smart Lock | `shared/integrations/ttlock.py`, `app/webhooks/ttlock.py` | — (bot notifications) |
| FR29-FR42 Apartment Mgmt | `app/api/routes/apartments.py`, `shared/crud/apartments.py` | `_layout/apartments.tsx`, `components/Host/` |
| FR32-FR33 Calendar Sync | `shared/integrations/calendar.py`, `workers/tasks/calendar_sync.py` | — |
| FR43-FR50 Reviews | `app/api/routes/reviews.py`, `shared/crud/reviews.py` | `components/Review/` |
| FR51-FR55 Communication | `bot/handlers/`, `workers/tasks/notifications.py` | — (Telegram) |
| FR56-FR62 Admin | `app/api/routes/admin.py` | `_layout/admin.tsx` |

### External Integration Points

| Сервис | Client Library | Location |
|--------|---------------|----------|
| Telegram Bot API | aiogram 3.24.0 | `bot/main.py` |
| Telegram Mini App | @telegram-apps/sdk 3.x | `lib/telegram.ts` |
| TTLock API | httpx | `shared/integrations/ttlock.py` |
| Google Calendar API | httpx | `shared/integrations/calendar.py` |
| Kaspi (manual) | — | `shared/integrations/kaspi.py` |
| Cloudflare R2 | aioboto3 | `shared/integrations/r2.py` |
| Sentry | sentry-sdk | `app/main.py` |

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
Все технологические решения совместимы: FastAPI async + asyncpg 0.31.0 + SQLModel работают как единый async стек. Redis 8 покрывает sessions, holds, rate limiting, arq queue. Vite 7.3 + React 19 + TanStack Router/Query — проверенная связка. aiogram 3.24.0 нативно async, один язык с backend.

**Pattern Consistency:**
Naming conventions (snake_case DB/API/JSON, PascalCase models/components) единообразны. Import convention (`from shared.models import ...`) работает для всех трёх consumers (app, bot, workers). Schema layer (`{Entity}Create/Public/Update`) применяется ко всем API endpoints.

**Structure Alignment:**
`shared/` на уровне `backend/` корректно обслуживает app, bot, workers без циклических зависимостей. Webhook routes вынесены из `/api/v1/` — внешние интеграции не зависят от версионирования API.

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**

| FR Cluster | Архитектурная поддержка | Статус |
|-----------|------------------------|--------|
| FR1-FR12 NLP Search | `app/nlp/` + `shared/crud/apartments.py` | ✅ |
| FR13-FR28 Booking + Payment | `shared/services/booking_service.py` + `payment_service.py` | ✅ |
| FR25-FR28a Smart Lock | `shared/integrations/ttlock.py` + 4-level fallback | ✅ |
| FR29-FR42 Apartment Mgmt | `app/api/routes/apartments.py` + dual-layout | ✅ |
| FR32-FR33 Calendar Sync | `shared/integrations/calendar.py` + arq worker | ✅ |
| FR43-FR50 Reviews | `app/api/routes/reviews.py` + `shared/crud/reviews.py` | ✅ |
| FR51-FR55 Communication | `bot/handlers/` + `workers/tasks/notifications.py` + двухуровневый FAQ | ✅ |
| FR56-FR62 Admin | `app/api/routes/admin.py` + `_layout/admin.tsx` | ✅ |

**Non-Functional Requirements Coverage:**

| NFR | Требование | Решение | Статус |
|-----|-----------|---------|--------|
| NFR-P1 | Bot ≤2 сек | Async FastAPI + Redis cache | ✅ |
| NFR-P8 | Real-time Admin | TanStack Query `refetchInterval: 10s` (MVP), SSE Phase 2 | ✅ Resolved |
| NFR-S6 | RPO ≤1h | Hourly `pg_dump` + cron, ротация 24 файла, daily → R2 | ✅ Resolved |
| NFR-S8 | Action-specific rate limits | Redis sliding window, per-action таблица лимитов | ✅ Resolved |
| NFR-SEC | Серверы в КЗ | Docker на KZ VPS (PS.kz / Selectel KZ) | ✅ |

### Implementation Readiness Validation ✅

**Decision Completeness:**
Все критические решения задокументированы с версиями (asyncpg 0.31.0, aiogram 3.24.0, Redis 8, PostgreSQL 18, Vite 7.3, React 19). Implementation patterns покрывают naming, structure, format, communication, process.

**Structure Completeness:**
Полное дерево проекта определено до уровня файлов. Все integration points указаны. Component boundaries (shared → app/bot/workers) зафиксированы.

**Pattern Completeness:**
DI patterns для FastAPI и non-FastAPI contexts. Schema layer convention. Import convention. arq job naming и payload rules. Test fixture naming.

### Gap Analysis Results (Party Mode Resolved)

**Все критические пробелы закрыты:**

| # | Пробел | Решение | Приоритет |
|---|--------|---------|-----------|
| 1 | NFR-P8: Real-time Admin updates | TanStack Query polling `refetchInterval: 10s` для MVP. SSE endpoint — Phase 2 | MVP |
| 2 | NFR-S6: Backup RPO ≤1h | Hourly `pg_dump` через cron, 24 файла ротация, daily full → R2, alert если backup > 2h | MVP |
| 3 | NFR-S8: Per-action rate limits | `shared/dependencies/rate_limit.py`, Redis sliding window counter | MVP |
| 4 | FR51: FAQ knowledge base | Глобальный `bot/data/faq.yaml` + per-apartment `faq: JSONB` в таблице apartment | MVP |

**Rate Limiting Table (Party Mode):**

| Action | Limit | Period | Redis Key |
|--------|-------|--------|-----------|
| search | 30 | 60s | `rate:{user_id}:search` |
| booking | 5 | 60s | `rate:{user_id}:booking` |
| payment | 3 | 60s | `rate:{user_id}:payment` |
| lock_op | 10 | 60s | `rate:{user_id}:lock` |
| auth | 5 | 300s | `rate:{ip}:auth` |

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High — все пробелы закрыты, решения проверены через Party Mode

**Key Strengths:**
- Unified async stack (FastAPI + asyncpg + aiogram + arq) — один event loop paradigm
- Shared code architecture — бизнес-логика пишется один раз, используется тремя consumers
- Production-ready шаблон (tiangolo) — CI/CD, Docker, тесты, auth из коробки
- Telegram-native: bot + Mini App + webhook — всё через один стек
- Чёткие patterns для AI-агентов — минимум конфликтов при параллельной разработке

**Areas for Future Enhancement:**
- SSE/WebSocket для real-time Admin updates (Phase 2)
- WAL archiving при росте базы >1GB
- Next.js landing для SEO (Phase 2, FR74)
- Full RBAC UI (Phase 2, FR70-71)
- Redis Streams fan-out для event broadcasting

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently across all components
- Respect project structure and boundaries (`shared/` → app/bot/workers)
- Refer to this document for all architectural questions
- Business logic lives in `shared/crud/` — routes/handlers are thin wrappers

**First Implementation Priority:**
1. Async DB migration (asyncpg + AsyncSession)
2. Redis в compose.yml
3. Telegram auth endpoint (`POST /api/v1/auth/telegram`)
4. Bot workspace (aiogram 3 + webhook)
