## 2026-08-13T17:51:00Z
<USER_REQUEST>
You are a test writer subagent assigned to write Tier 3 E2E Cross-Feature Combination tests for Tozalash Servis.

Your working directory is: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\e2e_test_writer_tier3
Target file to create: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\tests\e2e\test_tier3_cross_feature.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work.

Read the following requirement & scope documents first:
1. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\ORIGINAL_REQUEST.md
2. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\PROJECT.md
3. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\sub_orch_e2e_testing\SCOPE.md
4. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\TEST_INFRA.md

Task:
Implement AT LEAST 9 runnable pytest test cases covering pairwise cross-feature interactions in `tests/e2e/test_tier3_cross_feature.py`:
1. `test_cross_config_and_database_pool_init`: Config loading feeds MySQL aiomysql pool configuration and lazy lock setup.
2. `test_cross_bot_and_database_concurrency`: Bot and UserBot concurrent queries against aiomysql DB pool.
3. `test_cross_websocket_jwt_auth_and_config`: WebSocket server consuming JWT secrets from unified Pydantic Config.
4. `test_cross_ai_engine_and_vector_rag_storage`: AI LLM response generation automatically triggering vector_memory.store_interaction().
5. `test_cross_ai_engine_and_tts_audio_pipeline`: AI text output routed directly into Silero TTS synthesis and queue execution.
6. `test_cross_supervisor_and_bot_userbot_lifecycle`: Main task supervisor starting and gracefully stopping both PTB and Pyrogram userbot tasks.
7. `test_cross_guidelines_sync_and_ai_rotator`: Dynamic guidelines DB<->disk sync influencing AI prompt generation and rotator selection.
8. `test_cross_tts_worker_and_structured_logging`: Silero TTS worker execution producing PII-masked Loguru structured logs.
9. `test_cross_websocket_broadcast_and_ai_event_stream`: AI interaction events broadcasting real-time updates over authenticated WebSocket connections without data leaks.

Requirements:
- Ensure all test functions are named starting with `test_` and use `pytest` and `pytest-asyncio` (`@pytest.mark.asyncio`).
- Make tests robust, standalone, and executable via `python -m pytest tests/e2e/test_tier3_cross_feature.py`.
- Run `python -m pytest tests/e2e/test_tier3_cross_feature.py` using run_command to verify all 9+ tests pass without syntax or execution errors.
- Write a complete `handoff.md` report in `C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\e2e_test_writer_tier3\handoff.md` detailing the test suite, test count (≥9 tests), verification output, and status.
- Send a completion message back to parent using `send_message`.
</USER_REQUEST>
