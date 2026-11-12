# [Lesson 09] Add synthetic image batch normalization & applied questions (`R40-T060`)

## Summary

Extends "Building Image Generation Applications" in `09-building-image-applications/README.md` with a local `N x H x W` pixel validation and `0..255 -> 0..1` normalization lab (`09-building-image-applications/applied-labs/r40-t060/example.py`) and unit tests (`09-building-image-applications/applied-labs/r40-t060/test_example.py`).

- Preserves batch shape `(1, 2, 2)` on `[[[0, 255], [128, 64]]]`, maps `0 -> 0.0` and `255 -> 1.0`, and rejects negative or `> 255` pixels (`ValueError` / exit code `2`).
- Implements and verifies three applied questions (`q1_predict_output`, `q2_diagnose_failure`, `q3_boundary_policy`), each with a concise rationale and executable check.
- Explicitly states that this verifies preprocessing only—not model quality, real hardware, or cloud service behavior—using Python 3.9+ standard library only.

## Checks & Verification

All verification runs and recorded inputs, expected vs. actual results, and tool versions are stored in `work/R40-T060/`:

- Verification harness: `work/R40-T060/run_checks.py`
- Recorded results & tool versions: `work/R40-T060/check-results.json`
- Commands executed in fresh processes:
  - `python3 09-building-image-applications/applied-labs/r40-t060/example.py --case normal`
  - `python3 09-building-image-applications/applied-labs/r40-t060/example.py --case questions`
  - `python3 09-building-image-applications/applied-labs/r40-t060/example.py --case invalid_negative` (exits `2`)
  - `python3 09-building-image-applications/applied-labs/r40-t060/example.py --case invalid_over255` (exits `2`)
  - `python3 -m unittest discover -s 09-building-image-applications/applied-labs/r40-t060 -p "test_*.py"` (`Ran 5 tests`, `OK`, exit code `0`)
  - `python3 work/R40-T060/run_checks.py` (6 CLI cases + 5 unit tests + deliberate wrong-result failure confirming exit code `1` on `AssertionError`)

> **Note for upstreaming:** Remove `work/R40-T060/` on a later upstream branch before merging into upstream `main`.
