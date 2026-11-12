# [Lesson 02] Add whitespace-token budget fixture & controlled comparison (`R40-T058`)

## Summary

Extends "Exploring and comparing different LLMs" in `02-exploring-and-comparing-different-llms/README.md` with a deterministic local whitespace-token budget checker (`02-exploring-and-comparing-different-llms/applied-labs/r40-t058/example.py`) and unit tests (`02-exploring-and-comparing-different-llms/applied-labs/r40-t058/test_example.py`).

- Retains `["one", "two", "three"]` and reports `1` removed token (`truncated: true`) for `"one two three four"` at budget `3`; retains `[]` for empty input; rejects negative budgets (`ValueError` / exit code `2`).
- Explicitly labels the whitespace splitter (`str.split()`) as a teaching approximation, not a model's real subword/BPE tokenizer.
- Compares three small controlled budgets (`2`, `3`, `4`) using `token_retention_ratio` (`retained_count / input_token_count`), reporting correctness and the observed context-retention trade-off without claiming real-world model accuracy, latency, hardware, or cloud cost.

## Checks & Verification

All verification runs and recorded inputs, expected vs. actual results, and tool versions are stored in `work/R40-T058/`:

- Verification harness: `work/R40-T058/run_checks.py`
- Recorded results & tool versions: `work/R40-T058/check-results.json`
- Commands executed in fresh processes:
  - `python3 02-exploring-and-comparing-different-llms/applied-labs/r40-t058/example.py --case budget3`
  - `python3 02-exploring-and-comparing-different-llms/applied-labs/r40-t058/example.py --case compare`
  - `python3 02-exploring-and-comparing-different-llms/applied-labs/r40-t058/example.py --case empty`
  - `python3 02-exploring-and-comparing-different-llms/applied-labs/r40-t058/example.py --case negative` (exits `2`)
  - `python3 -m unittest discover -s 02-exploring-and-comparing-different-llms/applied-labs/r40-t058 -p "test_*.py"` (`Ran 5 tests`, `OK`, exit code `0`)
  - `python3 work/R40-T058/run_checks.py` (5 CLI scenarios + 5 unit tests + deliberate wrong-result failure confirming exit code `1` on `AssertionError`)

> **Note for upstreaming:** Remove `work/R40-T058/` on a later upstream branch before merging into upstream `main`.
