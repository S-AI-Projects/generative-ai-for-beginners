# [Lesson 01] Add startup decision table, error explanation & recovery (`R40-T059`)

## Summary

Extends "Introduction to Generative AI and Large Language Models" in `01-introduction-to-genai/README.md` with an original three-scenario worked example, decision-table checker, and invalid/missing-data error-and-recovery flow (`01-introduction-to-genai/applied-labs/r40-t059/example.py` and `test_example.py`).

- Represents `normal` (`serve_tutor_first_draft`), `boundary` (`shorten_or_split_prompt`), and `missing_info` (`halt_and_explain_missing_data`) as structured `input_facts`, explicit expected decisions, and rationales tied directly to Lesson 01 (`Scenario: our educational startup`, natural-language prompts, expanding `n`-token windows, and non-determinism/first-draft limits).
- Implements a deterministic decision-table checker (`check_decision_table` / `assert_decision_table`) that fails loudly (`AssertionError` / exit `1`) whenever any expected decision is deliberately altered.
- Exercises documented missing-data (`missing_info`) and invalid (`prompt_tokens=-5`) inputs through `StartupSessionProcessor`, explains each error cleanly without poisoning session state, and proves recovery to `serve_tutor_first_draft` on the next valid input.

## Checks & Verification

All verification runs and recorded inputs, expected vs. actual results, and tool versions are stored in `work/R40-T059/`:

- Verification harness: `work/R40-T059/run_checks.py`
- Recorded results & tool versions: `work/R40-T059/check-results.json`
- Commands executed in fresh processes:
  - `python3 01-introduction-to-genai/applied-labs/r40-t059/example.py --mode recovery`
  - `python3 01-introduction-to-genai/applied-labs/r40-t059/example.py --mode all`
  - `python3 01-introduction-to-genai/applied-labs/r40-t059/example.py --mode tamper` (exits `1`)
  - `python3 -m unittest discover -s 01-introduction-to-genai/applied-labs/r40-t059 -p "test_*.py"` (`Ran 4 tests`, `OK`, exit code `0`)
  - `python3 work/R40-T059/run_checks.py` (6 CLI modes + 4 unit tests + deliberate tampered-decision failure confirming exit code `1` on `AssertionError`)

> **Note for upstreaming:** Remove `work/R40-T059/` on a later upstream branch before merging into upstream `main`.
