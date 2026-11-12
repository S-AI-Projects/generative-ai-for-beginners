# [Lesson 14] Add local launch-config validation & secret redaction (`R40-T056`)

## Summary

Extends "The Generative AI Application Lifecycle" in `14-the-generative-ai-application-lifecycle/README.md` with a local preflight launch-configuration validator and secret redactor (`14-the-generative-ai-application-lifecycle/applied-labs/r40-t056/example.py`) and unit tests (`14-the-generative-ai-application-lifecycle/applied-labs/r40-t056/test_example.py`).

- Validates `command`, argument-array `args`, and explicit `env` key/value mappings; rejects missing `command` and single-string `args`; produces a redacted summary (`"launched": false`, `"<REDACTED>"` values) without launching any process.
- Implements a complete baseline (`validate_launch_config_baseline`), extracts `redact_env_values` as one named responsibility into `validate_launch_config`, preserves the exact contract (outputs and `ValueError` messages), and proves before/after equivalence across all fixtures.
- Uses Python 3.9+ standard library only and explicitly labels the lab as a local preflight simulation making no claims about real hardware, cloud services, or trained-model performance.

## Checks & Verification

All verification runs and recorded inputs, expected vs. actual results, and tool versions are stored in `work/R40-T056/`:

- Verification harness: `work/R40-T056/run_checks.py`
- Recorded results & tool versions: `work/R40-T056/check-results.json`
- Commands executed in fresh processes:
  - `python3 14-the-generative-ai-application-lifecycle/applied-labs/r40-t056/example.py --case valid`
  - `python3 14-the-generative-ai-application-lifecycle/applied-labs/r40-t056/example.py`
  - `python3 -m unittest discover -s 14-the-generative-ai-application-lifecycle/applied-labs/r40-t056 -p "test_*.py"` (`Ran 7 tests`, `OK`, exit code `0`)
  - `python3 work/R40-T056/run_checks.py` (4 targeted CLI scenarios + equivalence suite + 7 unit tests + deliberate wrong-result check confirming non-zero exit code `1` on `AssertionError`)

> **Note for upstreaming:** Remove `work/R40-T056/` on a later upstream branch before merging into upstream `main`.
