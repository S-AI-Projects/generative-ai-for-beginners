# [Lesson 19] Add local whitespace-token prompt-budget simulation (`R40-T053`)

## Summary

Extends "Introduction to Small Language Models for Generative AI for Beginners" in `19-slm/README.md` with a deterministic local whitespace-token prompt-budget simulation (`19-slm/applied-labs/r40-t053/example.py`) and unit tests (`19-slm/applied-labs/r40-t053/test_example.py`).

- Checks prompt token length against a configured non-negative budget, retaining `["one", "two", "three"]` and reporting `1` removed token (`["four"]`, `truncated: true`) for `"one two three four"` with budget `3`; retains none for empty/whitespace-only input; rejects negative budgets with `ValueError`.
- Explicitly labels the whitespace splitter (`prompt.split()`) as a **teaching approximation, not the model's real tokenizer**, and makes no claims about real hardware, cloud services, or trained-model performance.
- Compares the direct slice-based implementation (`check_prompt_budget`) against both a simpler independent calculation (`independent_budget_calculation`) and an explicit expected-result table (`EXPECTED_FIXTURE_TABLE`) on identical inputs.

## Checks & Verification

All verification runs and recorded inputs, expected vs. actual results, and tool versions are stored in `work/R40-T053/`:

- Verification harness: `work/R40-T053/run_checks.py`
- Recorded results & tool versions: `work/R40-T053/check-results.json`
- Commands executed in fresh processes:
  - `python3 19-slm/applied-labs/r40-t053/example.py --prompt "one two three four" --budget 3`
  - `python3 19-slm/applied-labs/r40-t053/example.py`
  - `python3 -m unittest discover -s 19-slm/applied-labs/r40-t053 -p "test_*.py"` (`Ran 6 tests`, `OK`, exit code `0`)
  - `python3 work/R40-T053/run_checks.py` (5 CLI scenarios + comparison table + 6 unit tests + deliberate wrong-result check confirming non-zero exit code `1` on `AssertionError`)

> **Note for upstreaming:** Remove `work/R40-T053/` on a later upstream branch before merging into upstream `main`.
