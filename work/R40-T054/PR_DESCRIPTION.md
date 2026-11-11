# [Lesson 11] Add streaming state trace & invariant simulation (`R40-T054`)

## Summary

Extends "Integrating with function calling" in `11-integrating-with-function-calling/README.md` with a local synthetic streaming state tracker (`11-integrating-with-function-calling/applied-labs/r40-t054/example.py`) and unit tests (`11-integrating-with-function-calling/applied-labs/r40-t054/test_example.py`).

- Models `pending`, `streaming`, `complete`, and `error` states for one response with a stable `message_id`, appending two chunks in order, preserving received text with `[ERROR: ...]` on failure, and rejecting chunks after completion (`ValueError`).
- Records an intermediate snapshot after every step (`LocalStreamingTracker.snapshots`)—including rejected post-completion attempts—and verifies trace-to-output invariants (`verify_trace_invariants`: `stable_message_id`, `monotonic_received_text`, `terminal_state_immutable`, `links_to_final_output`).
- Uses Python 3.9+ standard library only and explicitly labels the lab as a local in-memory simulation (`"simulation": true`) making no claims about real hardware, cloud services, or trained-model performance.

## Checks & Verification

All verification runs and recorded inputs, expected vs. actual results, and tool versions are stored in `work/R40-T054/`:

- Verification harness: `work/R40-T054/run_checks.py`
- Recorded results & tool versions: `work/R40-T054/check-results.json`
- Commands executed in fresh processes:
  - `python3 11-integrating-with-function-calling/applied-labs/r40-t054/example.py --scenario normal`
  - `python3 11-integrating-with-function-calling/applied-labs/r40-t054/example.py`
  - `python3 -m unittest discover -s 11-integrating-with-function-calling/applied-labs/r40-t054 -p "test_*.py"` (`Ran 7 tests`, `OK`, exit code `0`)
  - `python3 work/R40-T054/run_checks.py` (4 targeted CLI scenarios + default all + 7 unit tests + deliberate wrong-result check confirming non-zero exit code `1` on `AssertionError`)

> **Note for upstreaming:** Remove `work/R40-T054/` on a later upstream branch before merging into upstream `main`.
