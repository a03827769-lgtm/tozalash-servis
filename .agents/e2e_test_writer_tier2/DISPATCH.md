## 2026-08-13T17:51:00Z
<USER_REQUEST>
You are a test writer subagent assigned to write Tier 2 E2E Boundary & Corner Case tests for Tozalash Servis.

Your working directory is: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\e2e_test_writer_tier2
Target file to create: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\tests\e2e\test_tier2_boundary_corner.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work.

Read the following requirement & scope documents first:
1. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\ORIGINAL_REQUEST.md
2. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\PROJECT.md
3. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\sub_orch_e2e_testing\SCOPE.md
4. C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\TEST_INFRA.md

Task:
Implement EXACTLY 45 runnable pytest test cases (5 boundary/corner/error handling test cases per feature for features 1 to 9 in PROJECT.md) in `tests/e2e/test_tier2_boundary_corner.py`.
Cover:
- Feature 1 Boundary & Corner: Invalid env variable types, missing required secrets, malformed .env lines, whitespace handling, oversized config values.
- Feature 2 Boundary & Corner: DB connection timeout handling, uninitialized pool access attempt, missing detected_at column queries, migration rollback/re-entry error, concurrent connection exhaustion.
- Feature 3 Boundary & Corner: Supervisor exception cascades (unhandled subtask exception), abrupt process signal termination, double-start supervisor guard, corrupt session file recovery, thread starvation.
- Feature 4 Boundary & Corner: Bot vs UserBot port conflict attempts, double session file lock acquisition attempt, invalid bot token auth rejection, pyrogram disconnect recovery, concurrent message queue overflow.
- Feature 5 Boundary & Corner: WebSocket connection without token (401), invalid/expired JWT token, broadcast payload data leak prevention (message to unauth socket), socket abrupt disconnect cleanup, rapid connect/disconnect spam.
- Feature 6 Boundary & Corner: Deprecated/invalid Gemini model name handling, all rotator keys exhausted fallback, malformed JSON response parsing (truncated/extra braces), empty prompt input, API rate limit exponential backoff.
- Feature 7 Boundary & Corner: Empty client_id in store_interaction, disk dynamic_guidelines missing vs DB sync, corrupt RAG vector query input, genai file deletion non-existent file error, simultaneous guidelines read/write.
- Feature 8 Boundary & Corner: Silero model loading failure fallback, empty TTS text input, queue full scenario in _tts_worker, audio buffer overflow/underflow, voice agent destination phone format validation failure.
- Feature 9 Boundary & Corner: Loguru PII masking for nested dict/json strings, extremely large log line handling, corrupted requirements.txt parsing, missing dependency import error formatting, log file permission errors.

Requirements:
- Ensure all test functions are named starting with `test_` and use `pytest` and `pytest-asyncio` (`@pytest.mark.asyncio`).
- Make tests robust, standalone, and executable via `python -m pytest tests/e2e/test_tier2_boundary_corner.py`.
- Run `python -m pytest tests/e2e/test_tier2_boundary_corner.py` using run_command to verify all 45 tests pass without syntax or execution errors.
- Write a complete `handoff.md` report in `C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\e2e_test_writer_tier2\handoff.md` detailing the test suite, test count (45 tests), verification output, and status.
- Send a completion message back to parent using `send_message`.
</USER_REQUEST>
