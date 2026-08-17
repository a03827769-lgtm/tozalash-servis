## 2026-08-13T17:51:01Z
You are a test writer subagent assigned to write Tier 4 E2E Real-World Application Workload tests for Tozalash Servis.

Your working directory is: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\e2e_test_writer_tier4
Target file to create: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\tests\e2e\test_tier4_real_world.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work.

Read the following requirement & scope documents first:
1. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\ORIGINAL_REQUEST.md
2. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\PROJECT.md
3. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\sub_orch_e2e_testing\SCOPE.md
4. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\TEST_INFRA.md

Task:
Implement AT LEAST 5 runnable pytest test cases covering end-to-end real-world user & system workflows in `tests/e2e/test_tier4_real_world.py`:
1. `test_e2e_full_customer_cleaning_service_order_flow`: Complete customer journey: Config init -> Customer message via Bot -> AI pricing inquiry & competitor price lookup -> DB persistence -> WebSocket order creation broadcast.
2. `test_e2e_voice_agent_interactive_call_workflow`: Voice call journey: Incoming call request -> AI brain guideline lookup -> Silero TTS audio generation -> RAG interaction persistence -> Voice call completion.
3. `test_e2e_high_concurrency_websocket_and_bot_load`: System load scenario: 20 parallel WebSocket clients + Pyrogram UserBot monitoring + Telegram Bot customer requests under task supervisor without deadlock or memory leaks.
4. `test_e2e_database_migration_and_health_recovery_flow`: Maintenance scenario: System boot -> Migration 005 check -> Competitor price query with detected_at column -> Temporary DB pool drop & /health check degraded -> Automatic pool recovery.
5. `test_e2e_graceful_system_shutdown_and_resource_cleanup`: Operations scenario: Complete system startup with all services -> Simulated Windows shutdown signal -> Task supervisor cancellation -> Pyrogram session file unlock -> Clean exit without dangling background loops.

Requirements:
- Ensure all test functions are named starting with `test_` and use `pytest` and `pytest-asyncio` (`@pytest.mark.asyncio`).
- Make tests robust, standalone, and executable via `python -m pytest tests/e2e/test_tier4_real_world.py`.
- Run `python -m pytest tests/e2e/test_tier4_real_world.py` using run_command to verify all 5+ tests pass without syntax or execution errors.
- Write a complete `handoff.md` report in `C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\e2e_test_writer_tier4\handoff.md` detailing the test suite, test count (≥5 tests), verification output, and status.
- Send a completion message back to parent using `send_message`.
