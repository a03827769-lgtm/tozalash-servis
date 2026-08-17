# Scope: E2E Testing Track

## Architecture
Opaque-box, requirement-driven end-to-end testing suite for Tozalash Servis. The test suite verifies feature correctness, system stability, concurrency safety, API contracts, AI engine interactions, database integrity, and error handling without depending on internal private implementation details.

## Feature Inventory Mapping & Test Tier Partitioning
All 9 features from PROJECT.md are assigned across 4 test tiers:

| # | Feature | Scope / Verification Target | Tier 1 Tests | Tier 2 Tests | Tier 3 Tests | Tier 4 Tests |
|---|---------|-----------------------------|-------------|-------------|-------------|-------------|
| 1 | Config & Secrets Hygiene | Pydantic config validation, env parsing, PII sanitization, non-blocking boot | 5 | 5 | Pairwise | Workload |
| 2 | DB Schema & Connection Management | aiomysql pool init, Database._lock lazy load, competitor_prices.detected_at, /health pool access, migration 005 | 5 | 5 | Pairwise | Workload |
| 3 | Core Async Supervision & Startup | main.py task supervisor, exception safety, Windows shutdown signals, session locks | 5 | 5 | Pairwise | Workload |
| 4 | Telegram Bot & UserBot Concurrency | PTB v20.7 & Pyrogram parallel lifecycle, lock isolation, session file locking | 5 | 5 | Pairwise | Workload |
| 5 | Unified Authenticated WebSocket Server | JWT auth on /ws, connection manager, targeted broadcast isolation, fallback imports | 5 | 5 | Pairwise | Workload |
| 6 | AI LLM Engine & Rotator Fixes | Gemini model names (1.5-flash, 2.0-flash), rotator key cycling, non-greedy JSON parser | 5 | 5 | Pairwise | Workload |
| 7 | Vector Memory RAG & Guidelines Storage | RAG store_interaction, dynamic_guidelines disk<->DB sync, file deletion cleanup | 5 | 5 | Pairwise | Workload |
| 8 | Optimized TTS & Audio Pipeline | Silero model caching, thread offloading, _tts_worker queue safety, voice call routing | 5 | 5 | Pairwise | Workload |
| 9 | Structured Logging & Dependency Hygiene | Loguru PII masking, requirements.txt hygiene, log rotation, structured JSON logging | 5 | 5 | Pairwise | Workload |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E-M1 | Tier 1 E2E Test Suite | 45 Feature Coverage E2E tests (5 per feature) in `tests/e2e/test_tier1_feature_coverage.py` | none | DONE |
| E2E-M2 | Tier 2 E2E Test Suite | 45 Boundary & Corner Case E2E tests (5 per feature) in `tests/e2e/test_tier2_boundary_corner.py` | E2E-M1 | DONE |
| E2E-M3 | Tier 3 E2E Test Suite | 10 Pairwise Cross-Feature Combination E2E tests in `tests/e2e/test_tier3_cross_feature.py` | E2E-M1, E2E-M2 | DONE |
| E2E-M4 | Tier 4 E2E Test Suite | 5 Real-World Application Scenario E2E tests in `tests/e2e/test_tier4_real_world.py` | E2E-M1, E2E-M2, E2E-M3 | DONE |
| E2E-M5 | Test Runner & Publication | Verify complete suite via `pytest tests/e2e/`, publish `TEST_READY.md` | E2E-M1..M4 | DONE |

## Interface Contracts & Entry Points
- Test Runner Entry Point: `pytest tests/e2e/ -v`
- Database Mock/Live Fixtures: `pytest.fixture` with async pool simulation or MySQL fallback.
- Async Loop & Service Supervisor Testing: `asyncio` event loop isolation per test.
