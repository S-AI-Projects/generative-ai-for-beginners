# R40-T024 — Verification Results

This report records the test inputs, expected versus actual outputs, exit codes, and verification status for Task R40-T024.
Focus: Record the intermediate state after each step and test the invariant linking that state to the final output.

---

## 1. Normal Scenario (Microsoft Foundry reasoning model `gpt-5-mini`)

Command:
```bash
python3 06-text-generation-apps/applied-labs/r40-t024/example.py --scenario normal
```

Expected Decision: `EXECUTE_REASONING_PIPELINE`

Actual Output:
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "scenario_type": "normal",
  "model_id": "gpt-5-mini",
  "decision": "EXECUTE_REASONING_PIPELINE",
  "rationale": "Successfully executed reasoning model 'gpt-5-mini' pipeline. In accordance with Lesson 06, temperature sampling was omitted, API credentials were authenticated via environment variables, and two-step context chaining safely synthesized recipes and shopping list within the 1200 token budget. Negative filter 'garlic' was strictly maintained across all intermediate states.",
  "total_tokens_consumed": 350,
  "token_budget": 1200,
  "final_text": "1. Oven-Roasted Chicken with Potatoes and Carrots:\nIngredients:\n- 4 chicken thighs\n- 2 potatoes, cut into cubes\n- 2 carrots, cut into cubes\n- 2 tablespoons olive oil\n- 1 teaspoon dried thyme\n- 1 teaspoon dried oregano\n- Salt and pepper, to taste\n\n2. Chicken and Potato Stew:\nIngredients:\n- 2 tablespoons olive oil\n- 1 onion, diced\n- 2 chicken breasts, cut into cubes\n- 2 potatoes, cut into cubes\n- 2 carrots, cut into cubes\n- 1 teaspoon dried oregano\n- 1 teaspoon dried thyme\n- 1 cup chicken broth\n- Salt and pepper, to taste\n\n3. Chicken and Potato Bake:\nIngredients:\n- 2 tablespoons olive oil\n- 2 chicken breasts, cut into cubes\n- 2 potatoes, cut into cubes\n- 2 carrots, cut into cubes\n- 1 onion, diced\n- 1 teaspoon dried oregano\n- 1 teaspoon dried thyme\n- 1 cup chicken broth\n- Salt and pepper, to taste\n\nShopping List:\n- Olive oil\n- Onion\n- Thyme\n- Oregano\n- Salt\n- Pepper\n- Chicken broth",
  "diagnostic_envelope": {},
  "invariants_summary": {
    "all_invariants_hold": true,
    "token_conservation": {
      "holds": true,
      "details": "Token conservation holds across all steps and within budget limit."
    },
    "allergen_exclusion": {
      "holds": true,
      "details": "Allergen 'garlic' is strictly absent in all intermediate and final outputs."
    },
    "context_chaining_lineage": {
      "holds": true,
      "details": "Chaining lineage intact: Step 4 embeds Step 3 context, and shopping list is disjoint from pantry."
    },
    "terminal_state_monotonicity": {
      "holds": true,
      "details": "Pipeline did not halt in Step 1; monotonicity holds."
    }
  }
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Model parameters follow Lesson 06 (no temperature on reasoning model, secrets isolated, multi-step chaining within token budget, allergy filter respected). All 4 formal invariants hold.

---

## 2. Boundary Scenario (Open Sampling Model `Llama-3.3-70B-Instruct` at Temperature Boundary)

Command:
```bash
python3 06-text-generation-apps/applied-labs/r40-t024/example.py --scenario boundary
```

Expected Decision: `EXECUTE_SAMPLING_BOUNDARY_PIPELINE`

Actual Output:
```json
{
  "scenario_id": "SCENARIO_BOUNDARY",
  "scenario_type": "boundary",
  "model_id": "Llama-3.3-70B-Instruct",
  "decision": "EXECUTE_SAMPLING_BOUNDARY_PIPELINE",
  "rationale": "Successfully executed sampling model 'Llama-3.3-70B-Instruct' at the creative temperature boundary of 1.0. Under the tight token budget limit of 150 tokens, primary generation consumed 150 tokens (100% capacity), reaching the boundary threshold. In accordance with Lesson 06 token budgeting, secondary context chaining was safely bypassed to prevent quota overflow, and intermediate states confirm full invariant satisfaction.",
  "total_tokens_consumed": 150,
  "token_budget": 150,
  "final_text": "1. Spiced Apple and Flour Pancakes:\nIngredients:\n- 1 cup flour\n- 1/2 tsp baking powder\n- 1/2 tsp baking soda\n- 1/4 tsp salt\n- 1 egg\n- 1 cup buttermilk\n- 1/4 cup melted butter\n- 1 Granny Smith apple, peeled and grated\n- 1/4 tsp cinnamon",
  "diagnostic_envelope": {},
  "invariants_summary": {
    "all_invariants_hold": true,
    "token_conservation": {
      "holds": true,
      "details": "Token conservation holds across all steps and within budget limit."
    },
    "allergen_exclusion": {
      "holds": true,
      "details": "Allergen 'sugar' is strictly absent in all intermediate and final outputs."
    },
    "context_chaining_lineage": {
      "holds": true,
      "details": "Step 4 chaining was skipped or halted; chaining lineage holds vacuously."
    },
    "terminal_state_monotonicity": {
      "holds": true,
      "details": "Pipeline did not halt in Step 1; monotonicity holds."
    }
  }
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Sampling model operates at maximum allowable temperature boundary (1.0). Primary generation reaches exact token capacity (150/150 tokens = 100%), safely bypassing secondary context chaining to avoid token truncation/overflow. All 4 formal invariants hold.

---

## 3. Missing Information Scenario (Unconfigured Secrets & Missing Facts)

Command:
```bash
python3 06-text-generation-apps/applied-labs/r40-t024/example.py --scenario missing
```

Expected Decision: `HALT_MISSING_PREREQUISITES`

Actual Output:
```json
{
  "scenario_id": "SCENARIO_MISSING_INFO",
  "scenario_type": "missing_information",
  "model_id": "gpt-5-mini",
  "decision": "HALT_MISSING_PREREQUISITES",
  "rationale": "Execution safely halted at Step 1 due to missing or incompatible prerequisites: missing fields=['AZURE_OPENAI_API_KEY / OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT', 'max_output_tokens', 'prompt_inputs.no_recipes', 'prompt_inputs.ingredients']; incompatible parameters=['temperature (reasoning models do not support temperature)']. Lesson 06 strictly requires separating secrets and API credentials via environment variables, specifying valid token limits, and avoiding sampling controls (temperature) on reasoning models.",
  "total_tokens_consumed": 0,
  "token_budget": null,
  "final_text": null,
  "diagnostic_envelope": {
    "missing_fields": [
      "AZURE_OPENAI_API_KEY / OPENAI_API_KEY",
      "AZURE_OPENAI_ENDPOINT",
      "max_output_tokens",
      "prompt_inputs.no_recipes",
      "prompt_inputs.ingredients"
    ],
    "incompatible_params": [
      "temperature (reasoning models do not support temperature)"
    ]
  },
  "invariants_summary": {
    "all_invariants_hold": true,
    "token_conservation": {
      "holds": true,
      "details": "Token conservation holds across all steps and within budget limit."
    },
    "allergen_exclusion": {
      "holds": true,
      "details": "No allergy filter specified; exclusion invariant vacuously satisfied."
    },
    "context_chaining_lineage": {
      "holds": true,
      "details": "Context chaining was not requested."
    },
    "terminal_state_monotonicity": {
      "holds": true,
      "details": "Terminal state monotonicity holds: downstream steps skipped, zero tokens emitted."
    }
  }
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Essential prerequisites are missing or incompatible (`AZURE_OPENAI_API_KEY`, prompt ingredients, and illegal `temperature` on reasoning model). The pipeline safely halts at Step 1, producing 0 tokens and no output.

---

## 4. Full Decision Table Checker

Command:
```bash
python3 06-text-generation-apps/applied-labs/r40-t024/example.py --check
```

Actual Output:
```json
{
  "status": "success",
  "total_scenarios": 3,
  "passed_scenarios": 3,
  "failed_scenarios": 0,
  "all_passed": true,
  "scenarios": [
    {
      "scenario_id": "SCENARIO_NORMAL",
      "scenario_type": "normal",
      "model_id": "gpt-5-mini",
      "expected_decision": "EXECUTE_REASONING_PIPELINE",
      "actual_decision": "EXECUTE_REASONING_PIPELINE",
      "matches_table": true,
      "rationale_valid": true,
      "missing_keywords": [],
      "invariants_hold": true,
      "total_tokens_consumed": 350,
      "token_budget": 1200,
      "status": "PASS",
      "rationale": "Successfully executed reasoning model 'gpt-5-mini' pipeline. In accordance with Lesson 06, temperature sampling was omitted, API credentials were authenticated via environment variables, and two-step context chaining safely synthesized recipes and shopping list within the 1200 token budget. Negative filter 'garlic' was strictly maintained across all intermediate states.",
      "state_trace_steps": 5
    },
    {
      "scenario_id": "SCENARIO_BOUNDARY",
      "scenario_type": "boundary",
      "model_id": "Llama-3.3-70B-Instruct",
      "expected_decision": "EXECUTE_SAMPLING_BOUNDARY_PIPELINE",
      "actual_decision": "EXECUTE_SAMPLING_BOUNDARY_PIPELINE",
      "matches_table": true,
      "rationale_valid": true,
      "missing_keywords": [],
      "invariants_hold": true,
      "total_tokens_consumed": 150,
      "token_budget": 150,
      "status": "PASS",
      "rationale": "Successfully executed sampling model 'Llama-3.3-70B-Instruct' at the creative temperature boundary of 1.0. Under the tight token budget limit of 150 tokens, primary generation consumed 150 tokens (100% capacity), reaching the boundary threshold. In accordance with Lesson 06 token budgeting, secondary context chaining was safely bypassed to prevent quota overflow, and intermediate states confirm full invariant satisfaction.",
      "state_trace_steps": 5
    },
    {
      "scenario_id": "SCENARIO_MISSING_INFO",
      "scenario_type": "missing_information",
      "model_id": "gpt-5-mini",
      "expected_decision": "HALT_MISSING_PREREQUISITES",
      "actual_decision": "HALT_MISSING_PREREQUISITES",
      "matches_table": true,
      "rationale_valid": true,
      "missing_keywords": [],
      "invariants_hold": true,
      "total_tokens_consumed": 0,
      "token_budget": null,
      "status": "PASS",
      "rationale": "Execution safely halted at Step 1 due to missing or incompatible prerequisites: missing fields=['AZURE_OPENAI_API_KEY / OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT', 'max_output_tokens', 'prompt_inputs.no_recipes', 'prompt_inputs.ingredients']; incompatible parameters=['temperature (reasoning models do not support temperature)']. Lesson 06 strictly requires separating secrets and API credentials via environment variables, specifying valid token limits, and avoiding sampling controls (temperature) on reasoning models.",
      "state_trace_steps": 5
    }
  ]
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 3 canonical scenarios pass table matching, educational rationale validation, and invariant checks.

---

## 5. Intermediate State Trace Inspection (--trace)

Command:
```bash
python3 06-text-generation-apps/applied-labs/r40-t024/example.py --scenario normal --trace
```

Actual Output (Truncated State Trace Summary):
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "decision": "EXECUTE_REASONING_PIPELINE",
  "total_tokens_consumed": 350,
  "state_trace_summary": [
    {
      "step_index": 1,
      "step_name": "STEP_1_VALIDATION_AND_CONFIG",
      "status": "SUCCESS",
      "step_tokens_generated": 0,
      "cumulative_tokens": 0
    },
    {
      "step_index": 2,
      "step_name": "STEP_2_PROMPT_CONSTRUCTION",
      "status": "SUCCESS",
      "step_tokens_generated": 0,
      "cumulative_tokens": 0
    },
    {
      "step_index": 3,
      "step_name": "STEP_3_PRIMARY_GENERATION",
      "status": "SUCCESS",
      "step_tokens_generated": 240,
      "cumulative_tokens": 240
    },
    {
      "step_index": 4,
      "step_name": "STEP_4_CONTEXT_CHAINING",
      "status": "SUCCESS",
      "step_tokens_generated": 110,
      "cumulative_tokens": 350
    },
    {
      "step_index": 5,
      "step_name": "STEP_5_FINAL_ASSEMBLY",
      "status": "SUCCESS",
      "step_tokens_generated": 0,
      "cumulative_tokens": 350
    }
  ],
  "invariants_summary": {
    "all_invariants_hold": true,
    "token_conservation": {
      "holds": true,
      "details": "Token conservation holds across all steps and within budget limit."
    },
    "allergen_exclusion": {
      "holds": true,
      "details": "Allergen 'garlic' is strictly absent in all intermediate and final outputs."
    },
    "context_chaining_lineage": {
      "holds": true,
      "details": "Chaining lineage intact: Step 4 embeds Step 3 context, and shopping list is disjoint from pantry."
    },
    "terminal_state_monotonicity": {
      "holds": true,
      "details": "Pipeline did not halt in Step 1; monotonicity holds."
    }
  }
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Intermediate states sequentially recorded across all 5 discrete pipeline stages with monotonic token accumulation and invariant verification.

---

## 6. Deliberate Tamper Failure Verification

Command:
```bash
python3 06-text-generation-apps/applied-labs/r40-t024/example.py --deliberate-tamper SCENARIO_NORMAL
```

Actual Stderr:
```text
[DEMO] Mutated 'SCENARIO_NORMAL' expected decision from 'EXECUTE_REASONING_PIPELINE' to 'DELIBERATELY_MUTATED_WRONG_DECISION'
[EXPECTED FAILURE CONFIRMED] DecisionMismatchError caught: Scenario 'SCENARIO_NORMAL' decision mismatch: expected 'DELIBERATELY_MUTATED_WRONG_DECISION', got 'EXECUTE_REASONING_PIPELINE'
```

Exit code: `1` (Expected non-zero: `1`)

**Result:** PASS — Deliberately changing a decision in the published table triggers `DecisionMismatchError` and immediately exits non-zero (exit code 1).

---

## 7. Automated Unit Test Suite Discovery

Command:
```bash
python3 -m unittest discover -s 06-text-generation-apps/applied-labs/r40-t024 -p "test_*.py" -v
```

Actual Output (Stderr Summary):
```text
test_boundary_scenario_records_boundary_saturation_in_step_4 (test_example.TestIntermediateStateTracing.test_boundary_scenario_records_boundary_saturation_in_step_4)
Verifies boundary scenario traces step 4 with BOUNDARY_SATURATED status. ... ok
test_missing_info_records_halt_and_skips_downstream (test_example.TestIntermediateStateTracing.test_missing_info_records_halt_and_skips_downstream)
Verifies missing-information scenario records HALTED in step 1 and SKIPPED for 2-5. ... ok
test_normal_scenario_records_all_five_steps (test_example.TestIntermediateStateTracing.test_normal_scenario_records_all_five_steps)
Verifies that the normal scenario traces exactly 5 sequential steps. ... ok
test_step_payload_contents (test_example.TestIntermediateStateTracing.test_step_payload_contents)
Verifies specific payloads captured across intermediate states in normal scenario. ... ok
test_checker_fails_when_boundary_decision_tampered (test_example.TestPublishedDecisionTableAndChecker.test_checker_fails_when_boundary_decision_tampered)
Tampering with boundary scenario expected decision raises DecisionMismatchError. ... ok
test_checker_fails_when_missing_info_decision_tampered (test_example.TestPublishedDecisionTableAndChecker.test_checker_fails_when_missing_info_decision_tampered)
Tampering with missing_info scenario expected decision raises DecisionMismatchError. ... ok
test_checker_fails_when_normal_decision_tampered (test_example.TestPublishedDecisionTableAndChecker.test_checker_fails_when_normal_decision_tampered)
Tampering with normal scenario expected decision raises DecisionMismatchError. ... ok
test_checker_passes_on_canonical_table (test_example.TestPublishedDecisionTableAndChecker.test_checker_passes_on_canonical_table)
Untouched published decision table must pass all checks. ... ok
test_checker_soft_failure_reporting (test_example.TestPublishedDecisionTableAndChecker.test_checker_soft_failure_reporting)
When fail_on_tamper=False, checker returns failure dict instead of raising. ... ok
test_allergen_exclusion_invariant_fails_on_leak (test_example.TestStateInvariants.test_allergen_exclusion_invariant_fails_on_leak)
Allergen exclusion fails if an allergen leaks into intermediate recipe text. ... ok
test_allergen_exclusion_invariant_valid (test_example.TestStateInvariants.test_allergen_exclusion_invariant_valid)
Allergen exclusion holds when excluded allergen is strictly absent. ... ok
test_context_chaining_lineage_fails_when_lineage_broken (test_example.TestStateInvariants.test_context_chaining_lineage_fails_when_lineage_broken)
Context chaining fails if Step 4 input prompt loses Step 3 recipe context. ... ok
test_context_chaining_lineage_fails_when_pantry_item_in_shopping_list (test_example.TestStateInvariants.test_context_chaining_lineage_fails_when_pantry_item_in_shopping_list)
Context chaining fails if an ingredient in the pantry is included in shopping list. ... ok
test_context_chaining_lineage_invariant_valid (test_example.TestStateInvariants.test_context_chaining_lineage_invariant_valid)
Context chaining lineage holds when Step 4 embeds Step 3 text and pantry is disjoint. ... ok
test_terminal_state_monotonicity_fails_if_tokens_emitted_after_halt (test_example.TestStateInvariants.test_terminal_state_monotonicity_fails_if_tokens_emitted_after_halt)
Terminal monotonicity fails if non-zero tokens are emitted despite halt. ... ok
test_terminal_state_monotonicity_invariant_valid (test_example.TestStateInvariants.test_terminal_state_monotonicity_invariant_valid)
Terminal state monotonicity holds on missing information scenario. ... ok
test_token_budget_exceeded_fails_invariant (test_example.TestStateInvariants.test_token_budget_exceeded_fails_invariant)
Token conservation fails if total tokens exceeds the configured budget. ... ok
test_token_conservation_invariant_fails_on_tampered_step_tokens (test_example.TestStateInvariants.test_token_conservation_invariant_fails_on_tampered_step_tokens)
Token conservation fails if an intermediate step's tokens are tampered with. ... ok
test_token_conservation_invariant_valid (test_example.TestStateInvariants.test_token_conservation_invariant_valid)
Token conservation holds when step sums equal total tokens and within budget. ... ok
test_cli_default_check_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_default_check_exit_0) ... ok
test_cli_deliberate_tamper_fails_with_nonzero_exit (test_example.TestSubprocessCLIExecution.test_cli_deliberate_tamper_fails_with_nonzero_exit) ... ok
test_cli_scenario_boundary_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_boundary_exit_0) ... ok
test_cli_scenario_missing_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_missing_exit_0) ... ok
test_cli_scenario_normal_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_normal_exit_0) ... ok
test_cli_trace_flag (test_example.TestSubprocessCLIExecution.test_cli_trace_flag) ... ok
test_boundary_scenario_decision_and_rationale (test_example.TestThreeScenarios.test_boundary_scenario_decision_and_rationale) ... ok
test_missing_info_scenario_decision_and_rationale (test_example.TestThreeScenarios.test_missing_info_scenario_decision_and_rationale) ... ok
test_normal_scenario_decision_and_rationale (test_example.TestThreeScenarios.test_normal_scenario_decision_and_rationale) ... ok

----------------------------------------------------------------------
Ran 28 tests in 0.143s

OK
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 28 automated tests passed in a fresh process, testing state tracing, individual invariant violations, scenario rationales, tamper detection, and subprocess execution.

---

## 8. Summary of Contribution & Invariant Verification

| Scenario | Model Family | Decision | State Trace Steps | Tokens Consumed | All Invariants Hold? |
|---|---|---|---|---|---|
| `SCENARIO_NORMAL` | Reasoning (`gpt-5-mini`) | `EXECUTE_REASONING_PIPELINE` | 5 | 350 / 1200 | **YES** |
| `SCENARIO_BOUNDARY` | Sampling (`Llama-3.3-70B`) | `EXECUTE_SAMPLING_BOUNDARY_PIPELINE` | 5 | 150 / 150 | **YES** |
| `SCENARIO_MISSING_INFO` | Reasoning (`gpt-5-mini`) | `HALT_MISSING_PREREQUISITES` | 5 (1 Halted, 4 Skipped) | 0 / None | **YES** |

All checks passed successfully. Verification complete.
