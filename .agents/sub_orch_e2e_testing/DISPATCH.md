# DISPATCH

## 2026-08-13T17:50:33Z

Identity: sub_orch_e2e_testing
Role: E2E Testing Track Orchestrator
Working directory: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\sub_orch_e2e_testing

Scope:
Design and build a comprehensive, opaque-box, requirement-driven E2E test suite for the Tozalash Servis project based on user requirements in C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\ORIGINAL_REQUEST.md and C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\PROJECT.md.

Instructions:
1. Read ORIGINAL_REQUEST.md and PROJECT.md.
2. Create SCOPE.md in C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\sub_orch_e2e_testing\SCOPE.md and TEST_INFRA.md at C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\TEST_INFRA.md following the 4-tier test case methodology.
3. Delegate test writing to teamwork_preview_test_writer or teamwork_preview_worker subagents.
4. Design and implement runnable pytest E2E test cases in tests/ e.g. tests/e2e/ covering all 9 features from PROJECT.md:
   - Tier 1: Feature Coverage (>=5 per feature)
   - Tier 2: Boundary & Corner Cases (>=5 per feature)
   - Tier 3: Cross-Feature Combinations (pairwise)
   - Tier 4: Real-World Application Scenarios
5. Publish TEST_READY.md at project root (C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\TEST_READY.md) when complete with runner command and coverage checklist.
6. Send completion message to parent when TEST_READY.md is published.
