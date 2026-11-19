# Applied Lab (R40-T024): Worked Decision Example for "Building Text Generation Applications" — Intermediate State Tracing and Invariant Verification

This hands-on applied lab extends Lesson 06 (**Building Text Generation Applications**) with a local contract fixture modeling request governance, intermediate state tracing, and formal invariant verification across multi-step text generation pipelines.

---

## 1. Context & Lesson Connection

In Lesson 06 ([Building Text Generation Applications](../../README.md#building-text-generation-applications)), the curriculum teaches how to build generative AI applications using the modern OpenAI / Microsoft Foundry client libraries.

Key concepts from the lesson include:
1. **Transition to Text Generation Applications:** Unlike limited command-line or fixed UI apps, text generation applications accept flexible, unstructured natural language prompts and interact with large language models.
2. **Environment & Secret Separation:** Secrets (API keys and endpoints) must never be hardcoded into source files. They must be managed through environment variables (`AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `OPENAI_API_KEY`).
3. **Model Families & Sampling Parameter Compatibility:**
   - **Reasoning Models (e.g., `gpt-5-mini`, o-series):** Steered through prompt engineering, structured output, and reasoning controls. As established in Lesson 06, reasoning models **do not support sampling controls** (`temperature` or `top_p`) or `max_tokens`; passing `temperature` to a reasoning model yields an API error.
   - **Sampling / Open Models (e.g., `Llama-3.3-70B-Instruct`, Mistral):** Support `temperature` controls in the range $[0.0, 1.0]$, where $0.0$ maximizes predictability and $1.0$ represents the maximum creative variance boundary.
4. **Token Budgeting:** Output tokens incur cost and latency. Applications must economically configure `max_output_tokens` and manage token headroom across multi-step generation pipelines.
5. **Prompt Interpolation & Constraint Filtering:** Applications dynamically interpolate parameters into prompt templates (e.g., `no_recipes`, `ingredients`, and negative allergy filters like `no {filter}`).
6. **Multi-Step Prompt Chaining:** Applications pass previous generation outputs (`old_prompt_result`) as context into subsequent prompts (e.g., taking generated recipes and generating a shopping list excluding items already present in the kitchen pantry).

---

## 2. Contribution Focus: Intermediate State Tracing & Invariant Verification

This lab directly addresses the task focus:
> **"Record the intermediate state after each step and test the invariant linking that state to the final output."**

The application executes as a discrete 5-step state machine. After every single step, an immutable snapshot (`IntermediateState`) is recorded into a sequential execution trace (`state_trace`):

```
[Step 1: Validation & Config]
            │
            ▼  (Intermediate State 1 recorded: env secrets, model family, parameter compatibility)
[Step 2: Prompt Construction]
            │
            ▼  (Intermediate State 2 recorded: prompt interpolation, estimated prompt tokens, active filters)
[Step 3: Primary Generation]
            │
            ▼  (Intermediate State 3 recorded: recipe text, tokens consumed, allergen check)
[Step 4: Context Chaining]
            │
            ▼  (Intermediate State 4 recorded: token headroom check, chained prompt, shopping list items)
[Step 5: Final Assembly]
            │
            ▼  (Intermediate State 5 recorded: composite output assembly, invariant verification)
      [Final Output]
```

---

## 3. The Published Decision Table

The published decision table defines three canonical scenarios:

| Scenario ID | Type | Model & Family | Facts Summary | Expected Decision | Educational Rationale Highlight |
|---|---|---|---|---|---|
| `SCENARIO_NORMAL` | **Normal** | `gpt-5-mini`<br>(Reasoning) | Env secrets set; `temperature=None`; `max_output_tokens=1200`; prompt for 3 chicken/potato/carrot recipes with `filter_exclusion="garlic"`; `chain_shopping_list=True` | `EXECUTE_REASONING_PIPELINE` | Complies with Lesson 06 reasoning model guidance: omits `temperature`, authenticates via environment variables, safely chains recipe output into shopping list synthesis, and strictly excludes garlic across all states. |
| `SCENARIO_BOUNDARY` | **Boundary** | `Llama-3.3-70B-Instruct`<br>(Sampling) | Env secrets set; `temperature=1.0` (maximum boundary); `max_output_tokens=150` (tight boundary quota); prompt for 1 apple/flour recipe with `filter_exclusion="sugar"`; `chain_shopping_list=True` | `EXECUTE_SAMPLING_BOUNDARY_PIPELINE` | Complies with sampling model guidance: `temperature=1.0` is accepted for maximum variety; primary generation consumes exactly 150/150 tokens (100% capacity), exhausting headroom. Secondary chaining is safely bypassed to avoid overflow. |
| `SCENARIO_MISSING_INFO` | **Missing Information** | `gpt-5-mini`<br>(Reasoning) | Env secrets missing (`api_key=False`); invalid `temperature=0.7` passed to reasoning model; missing `max_output_tokens=None`; missing prompt facts (`ingredients=None`) | `HALT_MISSING_PREREQUISITES` | Violates prerequisite rules from Lesson 06: secrets are not isolated in environment, temperature is illegally passed to a reasoning model, and prompt facts are null. Pipeline safely halts at Step 1, producing 0 tokens and no output. |

---

## 4. Formal Invariants Linking Intermediate State to Final Output

Four formal invariants mathematically link the step-by-step intermediate state trace to the final output:

### Invariant 1: Token Conservation Invariant
$$\sum_{s \in \text{state\_trace}} s.\text{step\_tokens\_generated} = \text{total\_tokens\_consumed} \le \text{token\_budget}$$
The cumulative token count across intermediate generation steps must precisely match the final output's `total_tokens_consumed`, and must never exceed the configured `token_budget` (`max_output_tokens`).

### Invariant 2: Allergen Exclusion Invariant
$$\forall s \in \text{state\_trace}, \quad \text{filter\_exclusion} \notin s.\text{payload}[\text{text}] \quad \land \quad \text{filter\_exclusion} \notin \text{final\_output\_text}$$
If the user specifies an allergy or negative filter (e.g. `garlic` or `sugar`), that ingredient is strictly forbidden from appearing in Step 3 recipe text, Step 4 shopping list text, or the final assembled output.

### Invariant 3: Context Chaining Lineage Invariant
$$\text{Step 3 Recipe Text} \subseteq \text{Step 4 Input Context} \quad \land \quad \text{Pantry} \cap \text{ShoppingList} = \emptyset$$
When multi-step chaining is executed in Step 4, the input prompt must strictly embed the exact recipe text produced in Step 3 (`old_prompt_result`). Furthermore, all generated shopping list items must be strictly disjoint from the user's initial kitchen pantry ingredients.

### Invariant 4: Terminal State Monotonicity & Error Isolation Invariant
$$s_1.\text{status} = \text{HALTED} \implies \left( \forall i > 1, s_i.\text{status} = \text{SKIPPED} \right) \land \text{total\_tokens} = 0 \land \text{final\_text} = \text{None}$$
When prerequisite validation fails in Step 1, all downstream execution steps must be completely skipped, preventing any mock or real API token consumption and ensuring zero erroneous text is emitted.

---

## 5. Scope and Limitations (Simulation / Mock Scope)

- **Local Contract Fixture:** Implemented strictly using Python's standard library (`argparse`, `copy`, `datetime`, `enum`, `json`, `subprocess`, `sys`, `typing`, `unittest`).
- **Zero External Dependencies:** No `pip install`, virtual environment, or external package dependencies required.
- **Zero Real Cloud Resource Usage:** Requires no OpenAI/Azure subscription, paid credentials, local LLM weight downloads, or GPU/hardware acceleration.
- **Educational Boundary:** The fixture deterministic mock generators model the pipeline lifecycle, state machine transitions, and parameter compatibility rules taught in Lesson 06 without communicating over the network.

---

## 6. Usage & CLI Invocations

Run all commands from the repository root:

### 1. Run the Published Decision Table Checker

```bash
python3 06-text-generation-apps/applied-labs/r40-t024/example.py --check
```

**Expected Output (`exit 0`):**
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

### 2. Run a Single Scenario with Full Intermediate State Trace

```bash
python3 06-text-generation-apps/applied-labs/r40-t024/example.py --scenario normal --trace
```

### 3. Verify Deliberate Tamper Detection

To verify that the checker strictly fails with a non-zero exit code when an expected decision is deliberately altered:

```bash
python3 06-text-generation-apps/applied-labs/r40-t024/example.py --deliberate-tamper SCENARIO_NORMAL
```

**Expected Result (`exit 1`):**
```
[DEMO] Mutated 'SCENARIO_NORMAL' expected decision from 'EXECUTE_REASONING_PIPELINE' to 'DELIBERATELY_MUTATED_WRONG_DECISION'
[EXPECTED FAILURE CONFIRMED] DecisionMismatchError caught: Scenario 'SCENARIO_NORMAL' decision mismatch: expected 'DELIBERATELY_MUTATED_WRONG_DECISION', got 'EXECUTE_REASONING_PIPELINE'
```

### 4. Run the Automated Unit Test Suite

```bash
python3 -m unittest discover -s 06-text-generation-apps/applied-labs/r40-t024 -p "test_*.py"
```

All 28 unit tests pass in a fresh process, testing state tracing, individual invariants, scenario rationales, tamper detection, and CLI invocations.
