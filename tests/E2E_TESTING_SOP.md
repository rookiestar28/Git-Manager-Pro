# E2E Testing SOP

This repository has no frontend or Playwright harness. The user-facing replacement lane is
subprocess CLI integration testing plus platform smoke testing against disposable local fixtures.

## Replacement Procedure

1. Read `tests/TEST_SOP.md` and this notice.
2. Run `python scripts/run_cli_integration_tests.py` from the project-local venv.
3. Run the platform-specific disposable smoke command authorized for the roadmap item.
4. Record the platform, branch/base, candidate SHA, exact command, exit status, and redacted output.

The replacement lane must assert final CLI behavior, command routing, failure feedback, and side-effect
containment. A route-load or import-only check is insufficient.

## Platform Boundary

Windows and WSL/Linux are separate evidence lanes. A Windows run cannot be described as WSL/Linux
acceptance. If a platform is unavailable, record the missing receipt and leave the corresponding
roadmap criterion pending.
