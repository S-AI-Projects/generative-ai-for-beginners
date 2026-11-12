# [Lesson 01] Add three-scenario worked example & decision-table checker (`R40-T057`)

## Summary

Extends "Introduction to Generative AI and Large Language Models" in `01-introduction-to-genai/README.md` with an original three-scenario worked example for **"Scenario: our educational startup"** (`01-introduction-to-genai/applied-labs/r40-t057/example.py`) and regression tests (`01-introduction-to-genai/applied-labs/r40-t057/test_example.py`).

- Represents each scenario (`normal`, `boundary`, `missing_info`) with structured `input_facts`, an explicit expected decision (`approve_llm_draft`, `chunk_prompt_at_token_limit`, `request_missing_information`), a step-by-step worked trace, and a rationale tied directly to Lesson 01 concepts (natural-language prompts, token window limit `n`, non-determinism, and first-draft limitations).
- Implements a deterministic decision-table checker (`evaluate_decision_table` and `check_published_scenarios` / `assert_published_scenarios`) that executes the published 3-scenario example as a regression test and fails loudly (exit code `1` / `AssertionError`) when any decision is deliberately altered.
- Uses Python 3.9+ standard library only and explicitly labels the lab as a local static simulation making no claims about real hardware, cloud services, or trained-model performance.

## Checks & Verification

All verification runs and recorded inputs, expected vs. actual results, and tool versions are stored in `work/R40-T057/`:

- Verification harness: `work/R40-T057/run_checks.py`
- Recorded results & tool versions: `work/R40-T057/check-results.json`
- Commands executed in fresh processes:
  - `python3 01-introduction-to-genai/applied-labs/r40-t057/example.py --scenario normal`
  - `python3 01-introduction-to-genai/applied-labs/r40-t057/example.py`
  - `python3 01-introduction-to-genai/applied-labs/r40-t057/example.py --scenario normal --tamper-decision chunk_prompt_at_token_limit` (exits `1`)
  - `python3 -m unittest discover -s 01-introduction-to-genai/applied-labs/r40-t057 -p "test_*.py"` (`Ran 5 tests`, `OK`, exit code `0`)
  - `python3 work/R40-T057/run_checks.py` (all CLI scenarios + 5 unit tests + deliberate tampered-decision failure confirming exit code `1` on `AssertionError`)

> **Note for upstreaming:** Remove `work/R40-T057/` on a later upstream branch before merging into upstream `main`.
