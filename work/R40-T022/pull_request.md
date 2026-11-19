# Pull Request Title

```text
[Lesson 17] Add R40-T022 typed tool dispatch and boundary validation lab
```

---

# Pull Request Script & Description (.md)

```markdown
## Description
Student: Sarthak Chaudhary
Task: R40-T022 · 2 of 10
Issue: #22
Working Branch: `student/e26b07f0584/R40-T022`
Base Repository: `S-AI-Projects/generative-ai-for-beginners` (branch: `main`)
Head Repository: `Sarthak1179/generative-ai-for-beginners` (branch: `student/e26b07f0584/R40-T022`)

## Goal & Summary
This pull request extends the "Introduction" section of Lesson 17 (`17-ai-agents/README.md`) by introducing a hands-on local contract fixture (`17-ai-agents/applied-labs/r40-t022/`) that demonstrates defensive tool dispatch for AI agents:
- **Explicit Tool Allowlist:** Dispatches JSON calls strictly for `add(a, b)` and `multiply(a, b)`. Any undeclared tool name is rejected with a structured `UnknownToolError` (`TOOL_NOT_ALLOWED`).
- **Strict Numeric Argument Validation:** Both parameters `a` and `b` must be finite numbers (`int` or `float`). String arguments (e.g. `a = "2"`), boolean values (`True`/`False`), and non-finite numbers (`NaN`, `Infinity`) are rejected with a structured `ValidationError` (`INVALID_ARGUMENT_TYPE` or `NON_FINITE_NUMERIC_VALUE`).
- **Failure Isolation / Halting Rule:** In sequence/pipeline execution, a failed call halts execution immediately—a failed call cannot execute another tool, and all subsequent calls are marked as aborted.
- **Local Contract Fixture Scope:** Implemented using pure Python 3 standard library with zero external dependencies, no GPU, no model download, and no cloud provider credentials required. Explicitly marked as an educational contract fixture, not a full Model Context Protocol (MCP) transport.

---

## Exact Boundary Decisions & Rationale
1. **Smallest Valid Integers:** `add(0, 0) -> 0`, `multiply(0, 10) -> 0`. Zero is a valid identity and boundary element.
2. **Negative Arithmetic & Floats:** `add(-1, 1) -> 0`, `multiply(-2, 3) -> -6`, `multiply(2.5, 4.0) -> 10.0`. Negative numbers and fractional floats are preserved.
3. **Boolean Rejection:** In Python, `bool` subclasses `int` (`isinstance(True, int) == True`). However, in JSON and agent tool calling protocols, booleans and numbers are distinct primitives. Coercing boolean to numeric `1`/`0` is unsafe in agent tool dispatch; `bool` is strictly rejected.
4. **No String Coercion:** Strings representing numbers (`"2"`) are strictly rejected with a structured `ValidationError`. Automatic string-to-number coercion masks model hallucinations and schema drift.
5. **Non-Finite Number Rejection:** `NaN`, `Infinity`, and `-Infinity` are rejected because standard JSON (RFC 8259) prohibits non-finite numbers and they violate discrete arithmetic contracts.
6. **Execution Halting:** If call $k$ in a pipeline fails, execution terminates immediately, ensuring subsequent calls (e.g. `multiply`) are never invoked.

---

## Verification Evidence
All tests and checks pass in fresh processes:
- **Automated Test Suite:** `python3 -m unittest discover -s 17-ai-agents/applied-labs/r40-t022 -p "test_*.py" -v` reports 29 tests passed (`OK`).
- **Checks Script:** `python3 work/R40-T022/run_checks.py` validates all 9 scenarios and outputs results to `work/R40-T022/results.md`.
- **Deliberate Failure Test:** Verified that a deliberate wrong expectation (`assert result == 999`) strictly raises an `AssertionError` and exits with code 1.

---

## Done When Checklist

- [x] `add(2,3)→5; multiply(2,3)→6; unknown tool and string a are structured errors; a failed call cannot execute another tool. This is a local contract fixture, not a full MCP transport implementation.`
- [x] The lesson link and example agree on inputs, outputs and prerequisite tools.
- [x] The contribution focus is demonstrated, and a deliberate wrong result makes the test fail.
- [x] The example makes no unsupported claim about real hardware, cloud service behavior or trained-model performance.

## Submission Checklist

- [x] Complete this task and its checks.
- [x] Add the required evidence and link your pull request here.
- [x] Select this S-AI-Projects fork as the PR base repository.
- [x] Request instructor review.
- [x] Keep this PR focused on this task. Do not submit assignment PRs to the upstream repository.
```
