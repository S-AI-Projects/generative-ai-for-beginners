# [Lesson 21] Add local synthetic model-selection applied lab (`R40-T051`)

## Summary

Extends "Building With the Meta Family Models" in `21-meta/README.md` with a minimal, local synthetic model-selection lab (`21-meta/applied-labs/r40-t051/example.py`) and unit tests (`21-meta/applied-labs/r40-t051/test_example.py`).

- Evaluates a local synthetic manifest (`Fixture A`: 4 GB RAM / 2048 context; `Fixture B`: 8 GB RAM / 4096 context) against explicit `ram_budget_gb` (`6`) and `requested_context_tokens` (`1024`), admitting only `Fixture A` and reporting explicit failure reasons for `Fixture B`.
- Explicitly labels all fixtures and outputs as a local synthetic simulation (`"simulation": true`)—making no claims about real Meta Llama models, physical hardware requirements, cloud service behavior, or trained-model performance.
- Maps every public input and output of `select_eligible_models` to the lesson's memory-tier and context-window concepts.
- Requires only Python 3.9+ standard library (no model downloads, API keys, paid providers, GPUs, or physical devices).

## Checks & Verification

All verification runs and recorded inputs, expected vs. actual results, and tool versions are stored in `work/R40-T051/`:

- Verification harness: `work/R40-T051/run_checks.py`
- Recorded results & tool versions: `work/R40-T051/check-results.json`
- Commands executed in fresh processes:
  - `python3 21-meta/applied-labs/r40-t051/example.py` (admits only `Fixture A`, excludes `Fixture B` due to RAM budget)
  - `python3 -m unittest discover -s 21-meta/applied-labs/r40-t051 -p "test_*.py"` (`Ran 8 tests`, `OK`, exit code `0`)
  - `python3 work/R40-T051/run_checks.py` (6 CLI normal/boundary/failure scenarios + 8 unit tests + deliberate wrong-result check confirming non-zero exit code `1` on `AssertionError`)

> **Note for upstreaming:** Remove `work/R40-T051/` on a later upstream branch before merging into upstream `main`.
