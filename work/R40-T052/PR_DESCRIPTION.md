# [Lesson 11] Add local response streaming lifecycle simulation (`R40-T052`)

## Summary

Extends "Integrating with function calling" in `11-integrating-with-function-calling/README.md` with a local synthetic streaming state machine (`11-integrating-with-function-calling/applied-labs/r40-t052/example.py`) and unit tests (`11-integrating-with-function-calling/applied-labs/r40-t052/test_example.py`).

- Models `pending`, `streaming`, `complete`, and `error` states for one response with a stable `message_id`.
- Emphasizes the smallest valid case (two ordered chunks appending cleanly), boundary cases (error preserving partial received text with `[ERROR: ...]` marker, zero-chunk completion from `pending`, and empty-string deltas), and invalid cases (chunks after completion rejected with `ValueError` while preserving state).
- Documents the exact terminal-state and lower-bound decisions, connects each public input/output to the lesson's message-correlation and recovery concepts, and explicitly labels the lab as a local in-memory simulation using Python 3.9+ standard library only.

## Checks & Verification

All verification runs and recorded inputs, expected vs. actual results, and tool versions are stored in `work/R40-T052/`:

- Verification harness: `work/R40-T052/run_checks.py`
- Recorded results & tool versions: `work/R40-T052/check-results.json`
- Commands executed in fresh processes:
  - `python3 11-integrating-with-function-calling/applied-labs/r40-t052/example.py`
  - `python3 -m unittest discover -s 11-integrating-with-function-calling/applied-labs/r40-t052 -p "test_*.py"` (`Ran 7 tests`, `OK`, exit code `0`)
  - `python3 work/R40-T052/run_checks.py` (5 targeted CLI scenarios + full default suite + 7 unit tests + deliberate wrong-result check confirming non-zero exit code `1` on `AssertionError`)

> **Note for upstreaming:** Remove `work/R40-T052/` on a later upstream branch before merging into upstream `main`.
