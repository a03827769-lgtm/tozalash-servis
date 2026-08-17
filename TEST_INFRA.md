# E2E Test Infra: Tozalash Servis Cloud Deployment

## Test Philosophy
- Opaque-box, requirement-driven, and multi-tier verification.
- Validates cloud deployment readiness, container configurations, database and redis integrations, frontend builds, keepalive endpoints, and end-to-end user workflows.

## Feature Inventory & Test Coverage Mapping
| # | Feature | Requirement Source | Tier 1 (Feature) | Tier 2 (Boundary) | Tier 3 (Cross-Feature) | Tier 4 (Real-World) |
|---|---------|-------------------|:----------------:|:-----------------:|:----------------------:|:--------------------:|
| 1 | Unified Async Event Loop | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 2 | Dynamic Port & Host Binding | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 3 | Multi-Stage Dockerfile | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 4 | Clean Dockerignore | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 5 | Koyeb Deployment Config | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 6 | Render Deployment Config | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 7 | Graceful Signal Handling | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 8 | Cloud DATABASE_URL Parsing | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 9 | Supabase PgBouncer (6543) | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 10| Full 18-Table Schema Init | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 11| Database Business Methods | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 12| Endpoint Query Refactor | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 13| Upstash Redis 7 TLS & Resiliency | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 14| Cache Service Import | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 15| Active DB & Redis Healthcheck | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 16| Vercel Deployment Config | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 17| Real-Time WSS Client | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 18| Admin Panel Settings Page | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 19| Admin Panel Env Config | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 20| Internal Keepalive Self-Ping | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ | ✓ |
| 21| External Uptime Monitor Config | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ | ✓ |
| 22| Comprehensive Deployment Guide | ORIGINAL_REQUEST §R1-R4 | 5 | 5 | ✓ | ✓ |
| 23| Multi-Component .env.example | ORIGINAL_REQUEST §R1-R4 | 5 | 5 | ✓ | ✓ |
| 24| Automated Verification Script | ORIGINAL_REQUEST §R1-R4 | 5 | 5 | ✓ | ✓ |
| 25| Zero Regressions Across Test Suite | ORIGINAL_REQUEST §Acceptance | 5 | 5 | ✓ | ✓ |

## Test Architecture
- **Test Runner**: Pytest (`pytest -v`) + Next.js build validation (`npm run build`).
- **Smoke & Cloud Validator**: `scripts/verify_cloud_deployment.py` exercising database connections, Redis FSM, AI Brain, Telegram Bot initialization, and HTTP health check.
- **E2E Test Suites**:
  - `tests/e2e/test_tier1_features.py`: Happy-path feature verification in isolation.
  - `tests/e2e/test_tier2_boundaries.py`: Edge cases, invalid DSNs, connection disconnects, timeouts, malformed payloads.
  - `tests/e2e/test_tier3_pairwise.py`: Pairwise interactions (FastAPI + DB + Redis + WebSocket + Bot).
  - `tests/e2e/test_tier4_workloads.py`: Full realistic client order lifecycle, admin dashboard sync, and keepalive ping cycle.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Client Booking -> AI Analysis -> DB Persistence -> WebSocket Event -> Admin Dashboard Realtime Sync | F1, F8, F10, F13, F17 | High |
| 2 | Cloud Cold Start -> Self-Healthcheck -> PostgreSQL Connection Pool -> Redis Ping -> 200 OK | F1, F2, F8, F13, F15, F20 | Medium |
| 3 | Free-Tier Inactivity Keepalive Simulation (8-min loop self-ping and external probe) | F1, F15, F20, F21 | Medium |
| 4 | Next.js Frontend Static Prerender -> Vercel Edge Configuration -> WSS Reconnect on Network Drop | F16, F17, F19 | Medium |
| 5 | Database Failover & Resilient Fallback (Cloud DB Disconnect -> SQLite WAL Recovery) | F8, F10, F11, F13 | High |
