# [Lesson 06] Add R40-T024 text generation apps worked decision example and state trace lab

## Summary

This pull request implements the requirements for **Task R40-T024** by extending **Lesson 06: Building Text Generation Applications** (`06-text-generation-apps/README.md`) with a worked decision framework, intermediate state tracer, and invariant verification lab:

- **Intermediate State Tracing:** Implements a discrete 5-stage pipeline (`STEP_1_VALIDATION_AND_CONFIG` through `STEP_5_FINAL_ASSEMBLY`) in `example.py`, capturing immutable state snapshots after each step.
- **Formal Invariants:** Tests and enforces 4 invariants linking intermediate state to final output (Token Conservation, Allergen Exclusion, Context Chaining Lineage, and Terminal State Monotonicity).
- **Three Canonical Scenarios:** Defines a published decision table for a normal scenario (`gpt-5-mini` reasoning model), boundary scenario (`Llama-3.3-70B-Instruct` at temperature 1.0 with token budget saturation), and missing-information scenario (unconfigured credentials and prompt facts).
- **Tamper Detection & Automated Testing:** Includes a decision table checker that fails on deliberate decision mutations (`DecisionMismatchError`), supported by 28 automated unit tests and fresh-subprocess checks recorded in `work/R40-T024/results.md`.

## Checklists

### Done when
- [x] The normal scenario, a boundary scenario and a missing-information scenario each have an explicit expected decision. The checker must fail when a decision is deliberately changed; human review verifies that the rationale follows the lesson.
- [x] The lesson link and example agree on inputs, outputs and prerequisite tools.
- [x] The contribution focus is demonstrated, and a deliberate wrong result makes the test fail.
- [x] The example makes no unsupported claim about real hardware, cloud service behavior or trained-model performance.

### Submission checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
- [x] Keep this PR focused on this task. Do not submit assignment PRs to the upstream repository.
