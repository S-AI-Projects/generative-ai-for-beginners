# R40-T026 — Verification Results

This report records the test inputs, expected versus actual outputs, exit codes, and verification status for Task R40-T026.
Focus: Implement a correct baseline, then extract one named responsibility (`WordSetOverlapScorer`). Keep the same contract and prove before/after equivalence on the fixture.

---

## 1. Normal Scenario (`query='red apple'`)

Command:
```bash
python3 20-mistral/applied-labs/r40-t026/example.py --scenario normal
```

Expected Decision: `RETRIEVAL_SUCCESS_RANKED`
Expected Document Ranking: `['A', 'B']` (Scores: `[2, 1]`)

Actual Output:
```json
{
  "scenario_id": "SCENARIO_NORMAL",
  "scenario_type": "normal",
  "query": "red apple",
  "decision": "RETRIEVAL_SUCCESS_RANKED",
  "doc_ids": [
    "A",
    "B"
  ],
  "scores": [
    2,
    1
  ],
  "results": [
    {
      "doc_id": "A",
      "score": 2,
      "text": "red apple"
    },
    {
      "doc_id": "B",
      "score": 1,
      "text": "green apple"
    }
  ],
  "citation_block": "[Source A] (Score: 2): red apple\n[Source B] (Score: 1): green apple",
  "rationale": "Query 'red apple' overlaps Doc A on {'red', 'apple'} (score 2) and Doc B on {'apple'} (score 1). Ranks A before B with source attribution; Doc C ('blue sky') has 0 overlap and is omitted.",
  "classification": "lexical_test_double"
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Doc A ('red apple') achieves overlap 2, Doc B ('green apple') achieves overlap 1. Ranks A before B with source attribution; Doc C ('blue sky', overlap 0) is omitted.

---

## 2. Boundary Scenario (`query='ocean'`)

Command:
```bash
python3 20-mistral/applied-labs/r40-t026/example.py --scenario boundary
```

Expected Decision: `EMPTY_RESULT_NO_MATCH`
Expected Document Ranking: `[]` (Scores: `[]`)

Actual Output:
```json
{
  "scenario_id": "SCENARIO_BOUNDARY",
  "scenario_type": "boundary",
  "query": "ocean",
  "decision": "EMPTY_RESULT_NO_MATCH",
  "doc_ids": [],
  "scores": [],
  "results": [],
  "citation_block": "No relevant context found.",
  "rationale": "Query 'ocean' has zero word overlap with any document in the corpus. The retriever cleanly returns an empty match set [], avoiding hallucination or irrelevant prompt context.",
  "classification": "lexical_test_double"
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Query 'ocean' produces zero overlap across all corpus documents. Cleanly returns `[]`, preventing prompt hallucination.

---

## 3. Boundary Tie-Breaking Scenario (`query='apple'`)

Command:
```bash
python3 20-mistral/applied-labs/r40-t026/example.py --scenario tiebreak
```

Expected Decision: `RETRIEVAL_TIEBREAK_RESOLVED`
Expected Document Ranking: `['A', 'B']` (Scores: `[1, 1]`)

Actual Output:
```json
{
  "scenario_id": "SCENARIO_TIEBREAK",
  "scenario_type": "boundary",
  "query": "apple",
  "decision": "RETRIEVAL_TIEBREAK_RESOLVED",
  "doc_ids": [
    "A",
    "B"
  ],
  "scores": [
    1,
    1
  ],
  "results": [
    {
      "doc_id": "A",
      "score": 1,
      "text": "red apple"
    },
    {
      "doc_id": "B",
      "score": 1,
      "text": "green apple"
    }
  ],
  "citation_block": "[Source A] (Score: 1): red apple\n[Source B] (Score: 1): green apple",
  "rationale": "Query 'apple' matches Doc A and Doc B with identical score 1. The tie-breaking rule deterministically ranks Doc A before Doc B using document ID order ('A' < 'B').",
  "classification": "lexical_test_double"
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Overlap score is 1 for both Doc A and Doc B. Deterministic tie-breaking orders Doc A before Doc B based on ascending document ID.

---

## 4. Refactoring Equivalence Proof (`BaselineLexicalRetriever` vs `RefactoredLexicalRetriever`)

Command:
```bash
python3 20-mistral/applied-labs/r40-t026/example.py --prove-equivalence
```

Expected Status: `EQUIVALENCE_PROVEN` (`all_identical: true`)

Actual Output:
```json
{
  "status": "EQUIVALENCE_PROVEN",
  "total_queries_tested": 10,
  "all_identical": true,
  "comparisons": [
    {
      "query": "red apple",
      "baseline_count": 2,
      "refactored_count": 2,
      "match": true,
      "ranked_doc_ids": [
        "A",
        "B"
      ],
      "scores": [
        2,
        1
      ]
    },
    {
      "query": "ocean",
      "baseline_count": 0,
      "refactored_count": 0,
      "match": true,
      "ranked_doc_ids": [],
      "scores": []
    },
    {
      "query": "apple",
      "baseline_count": 2,
      "refactored_count": 2,
      "match": true,
      "ranked_doc_ids": [
        "A",
        "B"
      ],
      "scores": [
        1,
        1
      ]
    },
    {
      "query": "green apple",
      "baseline_count": 2,
      "refactored_count": 2,
      "match": true,
      "ranked_doc_ids": [
        "B",
        "A"
      ],
      "scores": [
        2,
        1
      ]
    },
    {
      "query": "blue sky",
      "baseline_count": 1,
      "refactored_count": 1,
      "match": true,
      "ranked_doc_ids": [
        "C"
      ],
      "scores": [
        2
      ]
    },
    {
      "query": "red",
      "baseline_count": 1,
      "refactored_count": 1,
      "match": true,
      "ranked_doc_ids": [
        "A"
      ],
      "scores": [
        1
      ]
    },
    {
      "query": "green",
      "baseline_count": 1,
      "refactored_count": 1,
      "match": true,
      "ranked_doc_ids": [
        "B"
      ],
      "scores": [
        1
      ]
    },
    {
      "query": "blue",
      "baseline_count": 1,
      "refactored_count": 1,
      "match": true,
      "ranked_doc_ids": [
        "C"
      ],
      "scores": [
        1
      ]
    },
    {
      "query": "apple sky",
      "baseline_count": 3,
      "refactored_count": 3,
      "match": true,
      "ranked_doc_ids": [
        "A",
        "B",
        "C"
      ],
      "scores": [
        1,
        1,
        1
      ]
    },
    {
      "query": "",
      "baseline_count": 0,
      "refactored_count": 0,
      "match": true,
      "ranked_doc_ids": [],
      "scores": []
    }
  ]
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Complete behavioral equivalence mathematically proven between the monolithic baseline and the refactored retriever using extracted `WordSetOverlapScorer` across 10 distinct queries.

---

## 5. Published Decision Table Checker

Command:
```bash
python3 20-mistral/applied-labs/r40-t026/example.py --check
```

Expected Status: `success` (`all_passed: true`, 4/4 scenarios)

Actual Output:
```json
{
  "status": "success",
  "total_scenarios": 4,
  "passed_scenarios": 4,
  "failed_scenarios": 0,
  "all_passed": true,
  "classification": "lexical_test_double",
  "scenarios": [
    {
      "scenario_id": "SCENARIO_NORMAL",
      "scenario_type": "normal",
      "expected_decision": "RETRIEVAL_SUCCESS_RANKED",
      "actual_decision": "RETRIEVAL_SUCCESS_RANKED",
      "matches_table": true,
      "status": "PASS",
      "doc_ids": [
        "A",
        "B"
      ],
      "scores": [
        2,
        1
      ],
      "rationale": "Query 'red apple' overlaps Doc A on {'red', 'apple'} (score 2) and Doc B on {'apple'} (score 1). Ranks A before B with source attribution; Doc C ('blue sky') has 0 overlap and is omitted."
    },
    {
      "scenario_id": "SCENARIO_BOUNDARY",
      "scenario_type": "boundary",
      "expected_decision": "EMPTY_RESULT_NO_MATCH",
      "actual_decision": "EMPTY_RESULT_NO_MATCH",
      "matches_table": true,
      "status": "PASS",
      "doc_ids": [],
      "scores": [],
      "rationale": "Query 'ocean' has zero word overlap with any document in the corpus. The retriever cleanly returns an empty match set [], avoiding hallucination or irrelevant prompt context."
    },
    {
      "scenario_id": "SCENARIO_TIEBREAK",
      "scenario_type": "boundary",
      "expected_decision": "RETRIEVAL_TIEBREAK_RESOLVED",
      "actual_decision": "RETRIEVAL_TIEBREAK_RESOLVED",
      "matches_table": true,
      "status": "PASS",
      "doc_ids": [
        "A",
        "B"
      ],
      "scores": [
        1,
        1
      ],
      "rationale": "Query 'apple' matches Doc A and Doc B with identical score 1. The tie-breaking rule deterministically ranks Doc A before Doc B using document ID order ('A' < 'B')."
    },
    {
      "scenario_id": "SCENARIO_EQUIVALENCE",
      "scenario_type": "equivalence",
      "expected_decision": "REFACTORING_EQUIVALENCE_PROVEN",
      "actual_decision": "REFACTORING_EQUIVALENCE_PROVEN",
      "matches_table": true,
      "status": "PASS",
      "doc_ids": null,
      "scores": null,
      "rationale": "BaselineLexicalRetriever and RefactoredLexicalRetriever (with extracted WordSetOverlapScorer) produce 100% identical ranked results, document IDs, and scores across all fixture queries."
    }
  ]
}
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — Canonical decision table fully validated across normal, boundary, tiebreak, and equivalence scenarios.

---

## 6. Deliberate Tamper & Wrong Result Detection

Command:
```bash
python3 20-mistral/applied-labs/r40-t026/example.py --tamper
```

Expected Exit Code: `1` (Non-zero exit on failure)

Actual Terminal Output:
```
[DEMO] Injecting deliberate tamper into SCENARIO_NORMAL expected decision...
[EXPECTED FAILURE CONFIRMED] Caught: Scenario 'SCENARIO_NORMAL' decision mismatch: expected 'DELIBERATELY_MUTATED_WRONG_DECISION', got 'RETRIEVAL_SUCCESS_RANKED'
```

Exit code: `1` (Expected: `1`)

**Result:** PASS — Deliberate alteration of expected scenario outcome is caught by `DecisionMismatchError` and exits with code 1, verifying that a deliberate wrong result strictly makes the verification fail.

---

## 7. Automated Unit Test Discovery Suite

Command:
```bash
python3 -m unittest discover -s 20-mistral/applied-labs/r40-t026 -p "test_*.py" -v
```

Expected Status: `OK` with non-zero test count

Actual Test Runner Output:
```
test_case_insensitivity (test_example.TestBaselineLexicalRetriever.test_case_insensitivity)
Uppercase query 'RED APPLE' must yield identical results to 'red apple'. ... ok
test_empty_and_whitespace_query (test_example.TestBaselineLexicalRetriever.test_empty_and_whitespace_query)
Empty or whitespace queries must return empty list without error. ... ok
test_punctuation_handling (test_example.TestBaselineLexicalRetriever.test_punctuation_handling)
Punctuation in query ('red, apple!') must be normalized away. ... ok
test_query_ocean_returns_no_match (test_example.TestBaselineLexicalRetriever.test_query_ocean_returns_no_match)
Query 'ocean' has zero overlap with all documents and must return empty list. ... ok
test_query_red_apple_ranks_a_before_b (test_example.TestBaselineLexicalRetriever.test_query_red_apple_ranks_a_before_b)
Query 'red apple' must score Doc A (2) before Doc B (1); Doc C omitted. ... ok
test_tie_breaking_by_doc_id (test_example.TestBaselineLexicalRetriever.test_tie_breaking_by_doc_id)
Query 'apple' ties Doc A (1) and Doc B (1); breaks tie by doc_id ('A' < 'B'). ... ok
test_before_after_equivalence_proven (test_example.TestBeforeAfterEquivalenceAndTamper.test_before_after_equivalence_proven)
Baseline and refactored retrievers must yield 100% identical outputs. ... ok
test_deliberate_wrong_result_makes_equivalence_test_fail (test_example.TestBeforeAfterEquivalenceAndTamper.test_deliberate_wrong_result_makes_equivalence_test_fail)
A deliberate alteration in ranking or scoring must trigger EquivalenceMismatchError. ... ok
test_checker_fails_when_boundary_tampered (test_example.TestCanonicalDecisionTableAndChecker.test_checker_fails_when_boundary_tampered) ... ok
test_checker_fails_when_decision_tampered (test_example.TestCanonicalDecisionTableAndChecker.test_checker_fails_when_decision_tampered) ... ok
test_checker_fails_when_doc_ids_tampered (test_example.TestCanonicalDecisionTableAndChecker.test_checker_fails_when_doc_ids_tampered) ... ok
test_checker_passes_on_canonical_table (test_example.TestCanonicalDecisionTableAndChecker.test_checker_passes_on_canonical_table) ... ok
test_format_citations_empty (test_example.TestCitationFormatting.test_format_citations_empty) ... ok
test_format_citations_with_results (test_example.TestCitationFormatting.test_format_citations_with_results) ... ok
test_score_convenience_method (test_example.TestExtractedWordSetOverlapScorer.test_score_convenience_method) ... ok
test_score_tokens_cardinality (test_example.TestExtractedWordSetOverlapScorer.test_score_tokens_cardinality) ... ok
test_score_tokens_empty (test_example.TestExtractedWordSetOverlapScorer.test_score_tokens_empty) ... ok
test_tokenize_empty (test_example.TestExtractedWordSetOverlapScorer.test_tokenize_empty) ... ok
test_tokenize_lowercase_word_sets (test_example.TestExtractedWordSetOverlapScorer.test_tokenize_lowercase_word_sets) ... ok
test_tokenize_punctuation_and_whitespace (test_example.TestExtractedWordSetOverlapScorer.test_tokenize_punctuation_and_whitespace) ... ok
test_custom_injected_scorer (test_example.TestRefactoredLexicalRetriever.test_custom_injected_scorer) ... ok
test_query_ocean_returns_no_match (test_example.TestRefactoredLexicalRetriever.test_query_ocean_returns_no_match) ... ok
test_query_red_apple_ranks_a_before_b (test_example.TestRefactoredLexicalRetriever.test_query_red_apple_ranks_a_before_b) ... ok
test_tie_breaking_by_doc_id (test_example.TestRefactoredLexicalRetriever.test_tie_breaking_by_doc_id) ... ok
test_cli_check_all_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_check_all_exit_0) ... ok
test_cli_prove_equivalence_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_prove_equivalence_exit_0) ... ok
test_cli_scenario_boundary_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_boundary_exit_0) ... ok
test_cli_scenario_normal_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_normal_exit_0) ... ok
test_cli_scenario_tiebreak_exit_0 (test_example.TestSubprocessCLIExecution.test_cli_scenario_tiebreak_exit_0) ... ok
test_cli_tamper_fails_with_nonzero_exit (test_example.TestSubprocessCLIExecution.test_cli_tamper_fails_with_nonzero_exit)
The --tamper flag must intentionally trigger an error and exit with code 1. ... ok

----------------------------------------------------------------------
Ran 30 tests in 0.157s

OK
```

Exit code: `0` (Expected: `0`)

**Result:** PASS — All 30 unit tests executed and passed in a fresh process.

---

## 8. Summary of Task Verification

| Scenario | Query | Expected Decision | Actual Decision | Ranked Doc IDs | Status |
|---|---|---|---|---|---|
| `SCENARIO_NORMAL` | `'red apple'` | `RETRIEVAL_SUCCESS_RANKED` | `RETRIEVAL_SUCCESS_RANKED` | `['A', 'B']` | **PASS** |
| `SCENARIO_BOUNDARY` | `'ocean'` | `EMPTY_RESULT_NO_MATCH` | `EMPTY_RESULT_NO_MATCH` | `[]` | **PASS** |
| `SCENARIO_TIEBREAK` | `'apple'` | `RETRIEVAL_TIEBREAK_RESOLVED` | `RETRIEVAL_TIEBREAK_RESOLVED` | `['A', 'B']` | **PASS** |
| `SCENARIO_EQUIVALENCE` | 10 Test Queries | `REFACTORING_EQUIVALENCE_PROVEN` | `REFACTORING_EQUIVALENCE_PROVEN` | Identical | **PASS** |
| `DELIBERATE_TAMPER` | Mutated Spec | Exit Code `1` | Exit Code `1` | N/A | **PASS** |

All checks passed successfully. Verification complete.
