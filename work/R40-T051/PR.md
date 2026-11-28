# PR: r40-t051 — resource-envelope eligibility lab (Meta family lesson)

Branch: `R40-T051` (committed locally as `8ea39f6e`).
Remote: the *organisation fork* `s-and-ai-ru-2/generative-ai-for-beginners`.
Status: **can not be pushed/created in this session** — see "Outcome" below.

## What changed

- `21-meta/README.md`
  - New linked section **Applied lab r40-t051 — selecting a model by RAM and context**.
  - Explains the lesson concept, the exact invocation, the fixture, the exact
    expected output, boundary/failure scenarios, a lesson-concept input/output
    mapping, and where the simplifications stop.
- `21-meta/applied-labs/r40-t051/example.py`
  - Minimal complete local example (stdlib only): `ModelVariant`, `is_eligible`,
    `eligibility_reason`, `select_models`, and `run_demo`.
  - Fixture A (RAM4 / context2048) vs Fixture B (RAM8 / context4096).
  - Budget RAM6 + context1024 admits only Fixture A (`8 > 6` excludes Fixture B).
- `21-meta/applied-labs/r40-t051/test_r40_t051.py`
  - 15 tests: normal, boundary, failure, empty manifest, zero envelope.
  - Negative budget/requested/manifest values raise `ValueError`.
  - Includes a deliberate-wrong-result assertion that must be rejected
    (`test_only_a_admitted`).
- `21-meta/applied-labs/r40-t051/check_r40_t051.py`
  - Runs `python3 -m unittest discover -s 21-meta/applied-labs/r40-t051 -p
    "test_*.py"` in a fresh subprocess.
  - Saves inputs / expected vs actual / tool versions under `work/R40-T051/`.
  - Self-test proves the check exits non-zero on failure (`assert False` →
    exit 1).

## Result

- `python3 21-meta/applied-labs/r40-t051/example.py` → prints
  `eligible=fixture-a` and `excluded=fixture-b why=exceeds budget RAM` (exit 0).
- `python3 -m unittest discover -s 21-meta/applied-labs/r40-t051 -p "test_*.py"`
  → `Ran 15 tests ... OK` (exit 0).

## Checks

- Check runner: `21-meta/applied-labs/r40-t051/check_r40_t051.py`
- Check outputs: `work/R40-T051/`
  - `inputs.json`, `expected.json`, `actual_example_output.txt`,
    `actual_unittest_output.txt`, `compared_actual_vs_expected.json`,
    `tool_versions.json`, `check_self_test.json`, `check_exit_code.txt`
- The example never downloads a model, calls a paid provider, uses a GPU, or
  accesses the network. RAM/context values are invented teaching fixtures.

## Outcome / blocker

`git push -u origin R40-T051` returned **HTTP 403** and `gh auth status` reports
"not logged into any GitHub hosts". The origin remote is the organisation fork,
and the generic `t9m487cjd8-creator` identity has no permission to push there.
This session therefore cannot create the PR itself. Push the branch and open the
PR manually when credentials are available, referencing issue #6:

```bash
# 1) Obtain your own fork (forks live on GitHub, not in git):
gh repo fork s-and-ai-ru-2/generative-ai-for-beginners --clone

# 2) Push the reviewable branch to your fork:
git push -u origin R40-T051          # if origin now resolves to your fork

# 3) Open the PR against the org fork, base main, issue #6:
gh pr create --repo s-and-ai-ru-2/generative-ai-for-beginners --base main \
  --title "r40-t051: resource-envelope eligibility lab (Meta family lesson)" \
  --body-file work/R40-T051/PR.md
```

Issue link: https://github.com/s-and-ai-ru-2/generative-ai-for-beginners/issues/6
