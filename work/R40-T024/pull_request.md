# Pull Request: [Lesson 06] Add R40-T024 text generation apps worked decision example and state trace lab

**Base Repository:** `S-AI-Projects/generative-ai-for-beginners` (`main`)  
**Head Repository:** `Sarthak1179/generative-ai-for-beginners` (`student/e26b07f0584/R40-T024` / `R40-T024`)  
**Student:** Sarthak Chaudhary  
**Task ID:** R40-T024 (4 of 10)  
**Issue Reference:** Closes #24  

---

## Description

This PR extends **Lesson 06: Building Text Generation Applications** ([06-text-generation-apps/README.md](https://github.com/S-AI-Projects/generative-ai-for-beginners/blob/main/06-text-generation-apps/README.md)) with a comprehensive, three-scenario worked decision framework, intermediate state tracer, and formal invariant verification system.

### Key Contributions

1. **Applied Lab ([06-text-generation-apps/applied-labs/r40-t024/](https://github.com/S-AI-Projects/generative-ai-for-beginners/tree/main/06-text-generation-apps/applied-labs/r40-t024/)):**
   - Implements a 5-stage state machine (`STEP_1_VALIDATION_AND_CONFIG`, `STEP_2_PROMPT_CONSTRUCTION`, `STEP_3_PRIMARY_GENERATION`, `STEP_4_CONTEXT_CHAINING`, `STEP_5_FINAL_ASSEMBLY`).
   - Captures immutable `IntermediateState` snapshots after every discrete step.
   - Enforces 4 formal mathematical and logical invariants linking intermediate state to final output:
     - **Token Conservation Invariant:** Sum of step tokens equals total tokens consumed $\le$ token budget.
     - **Allergen Exclusion Invariant:** Negative filter constraints (e.g. `garlic`, `sugar`) strictly do not leak into intermediate recipe text, intermediate shopping lists, or final outputs.
     - **Context Chaining Lineage Invariant:** Step 4 embeds Step 3 recipe context verbatim, and shopping list is strictly disjoint from user pantry ingredients.
     - **Terminal State Monotonicity Invariant:** Halting in Step 1 skips all downstream steps, produces 0 tokens, and emits `None` output.
2. **Three Canonical Scenarios:**
   - **Normal Scenario (`SCENARIO_NORMAL`):** Microsoft Foundry reasoning model (`gpt-5-mini`) adhering to Lesson 06 guidance (no temperature on reasoning models, environment secrets isolated, multi-step recipe-to-shopping-list chaining within 1200-token budget). Decision: `EXECUTE_REASONING_PIPELINE`.
   - **Boundary Scenario (`SCENARIO_BOUNDARY`):** Open sampling model (`Llama-3.3-70B-Instruct`) operating at maximum temperature boundary (`temperature=1.0`) and tight token capacity (`150` tokens). Satures token budget (150/150 = 100%), safely bypassing secondary chaining to prevent overflow. Decision: `EXECUTE_SAMPLING_BOUNDARY_PIPELINE`.
   - **Missing-Information Scenario (`SCENARIO_MISSING_INFO`):** Unconfigured environment secrets, illegal `temperature=0.7` passed to reasoning model, missing token budget, and missing prompt facts. Safely halts at Step 1 with diagnostic envelope. Decision: `HALT_MISSING_PREREQUISITES`.
3. **Decision Table Checker & Tamper Detection:**
   - The checker verifies all scenarios against the published decision table and asserts lesson-tied rationales.
   - When any decision is deliberately changed (tested via `--deliberate-tamper SCENARIO_NORMAL`), the checker immediately raises `DecisionMismatchError` and exits with code 1.
4. **Lesson Integration:**
   - Added linked section to [06-text-generation-apps/README.md](https://github.com/S-AI-Projects/generative-ai-for-beginners/blob/main/06-text-generation-apps/README.md) with exact CLI invocations, expected outputs, and simulation/mock scope notes.
5. **Automated Unit Test Suite:**
   - 28 unit tests in [06-text-generation-apps/applied-labs/r40-t024/test_example.py](https://github.com/S-AI-Projects/generative-ai-for-beginners/blob/main/06-text-generation-apps/applied-labs/r40-t024/test_example.py) testing all state tracing steps, invariant violations, scenario rationales, tamper detection, and subprocess execution.
6. **Verification Evidence (`work/R40-T024/`):**
   - Inputs, tool versions, test runner (`run_checks.py`), and execution logs in `results.md`.

---

## Verification Summary

All checks were executed in fresh subprocesses via `python3 work/R40-T024/run_checks.py`:

| Check | Target / Command | Exit Code | Result | Details |
|---|---|---|---|---|
| Check 1 | `--scenario normal` | `0` | **PASS** | `EXECUTE_REASONING_PIPELINE`, 350 tokens, all invariants hold |
| Check 2 | `--scenario boundary` | `0` | **PASS** | `EXECUTE_SAMPLING_BOUNDARY_PIPELINE`, 150/150 tokens, chaining bypassed safely |
| Check 3 | `--scenario missing` | `0` | **PASS** | `HALT_MISSING_PREREQUISITES`, 0 tokens, output `None` |
| Check 4 | `--check` | `0` | **PASS** | All 3 canonical scenarios pass table matching & rationales |
| Check 5 | `--scenario normal --trace` | `0` | **PASS** | 5 discrete steps verified with monotonic token consumption |
| Check 6 | `--deliberate-tamper SCENARIO_NORMAL` | `1` | **PASS** | Deliberate wrong result exits 1 with `DecisionMismatchError` |
| Check 7 | `unittest discover` | `0` | **PASS** | Ran 28 tests in 0.14s — OK |

---

## Checklist

### Done When Checklist
- [x] The normal scenario, a boundary scenario and a missing-information scenario each have an explicit expected decision. The checker must fail when a decision is deliberately changed; human review verifies that the rationale follows the lesson.
- [x] The lesson link and example agree on inputs, outputs and prerequisite tools.
- [x] The contribution focus is demonstrated, and a deliberate wrong result makes the test fail.
- [x] The example makes no unsupported claim about real hardware, cloud service behavior or trained-model performance.

### Submission Checklist
- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
- [x] Keep this PR focused on this task. Do not submit assignment PRs to the upstream repository.
