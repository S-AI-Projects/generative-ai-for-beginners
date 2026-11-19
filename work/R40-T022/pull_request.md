# [Lesson 17] Add R40-T022 typed tool dispatch and boundary validation lab

## Summary
- **Lesson Extension:** Extended "Introduction" in `17-ai-agents/README.md` with a linked applied lab section documenting exact tool invocations, argument schemas, expected JSON outputs, and simulation/mock scope notes.
- **Typed Dispatch Fixture:** Created `17-ai-agents/applied-labs/r40-t022/example.py` implementing an explicit allowlist for `add(a, b)` and `multiply(a, b)` with strict numeric validation (`int` and `float`).
- **Structured Error Handling:** Rejects unknown tools (`UnknownToolError`) and non-numeric/string arguments (`ValidationError`) with consistent JSON error envelopes. Booleans (`True`/`False`), numeric strings (e.g. `"2"`), and non-finite floats (`NaN`, `Infinity`) are strictly rejected.
- **Failure Isolation:** Enforced pipeline execution halting—a failed call immediately stops execution and prevents subsequent tools from running.
- **Verification & Testing:** Added `test_example.py` with 29 passing unit and integration tests, and recorded all verification checks and deliberate failure assertions in `work/R40-T022/results.md`.

## Done when
- [x] add(2,3)→5; multiply(2,3)→6; unknown tool and string a are structured errors; a failed call cannot execute another tool. This is a local contract fixture, not a full MCP transport implementation.
- [x] The lesson link and example agree on inputs, outputs and prerequisite tools.
- [x] The contribution focus is demonstrated, and a deliberate wrong result makes the test fail.
- [x] The example makes no unsupported claim about real hardware, cloud service behavior or trained-model performance.

## Submission checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
- [x] Keep this PR focused on this task. Do not submit assignment PRs to the upstream repository.
