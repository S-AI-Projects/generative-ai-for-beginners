# R40-T033 Check Evidence

## Tool Versions

- Python: 3.14.6 (verified via `python3 --version`)
- unittest: Standard library (no external packages or virtual environments needed)

## Inputs, Expected vs Actual Results

### Scenario 1 — Normal Scenario: Contract Fixture `query="red apple"`

Corpus:
- `A`: `"red apple"`
- `B`: `"green apple"`
- `C`: `"blue sky"`

| Field | Input Parameter | Expected Output | Actual Output |
|---|---|---|---|
| **Query** | `"red apple"` | N/A | Processed ✓ |
| **Result Count** | N/A | `2` (Doc C excluded) | `2` ✓ |
| **Rank 1 Document** | N/A | `doc_id="A"`, `score=2` | `doc_id="A"`, `score=2` ✓ |
| **Rank 2 Document** | N/A | `doc_id="B"`, `score=1` | `doc_id="B"`, `score=1` ✓ |
| **Relative Ranking** | N/A | A ranks before B | A ranks before B ✓ |
| **Document Attribution** | N/A | `doc_id` returned with each result | Returned ✓ |

### Scenario 2 — Empty Match Scenario: Query `"ocean"`

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Query** | `"ocean"` | `[]` (no match) | `[]` (no match) ✓ |
| **Result Count** | N/A | `0` | `0` ✓ |

### Scenario 3 — Deterministic Tie-Breaking by Document ID

Corpus: `{"DOC_Z": "golden fruit harvest", "DOC_A": "golden fruit basket", "DOC_M": "golden fruit garden"}`
Query: `"golden fruit"` (each document scores 2)

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Scores** | Equal (score 2 each) | Broken by `doc_id` ascending | Broken by `doc_id` ascending ✓ |
| **Ranked Order** | N/A | `["DOC_A", "DOC_M", "DOC_Z"]` | `["DOC_A", "DOC_M", "DOC_Z"]` ✓ |

### Scenario 4 — Failure Scenarios

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Non-string Query** | `123` | `TypeError` raised | `TypeError` raised ✓ |
| **Empty Document ID** | `""` | `ValueError` raised | `ValueError` raised ✓ |
| **Non-string Text** | `123` | `TypeError` raised | `TypeError` raised ✓ |

---

## Focus: Comparison with Independent Reference Oracle Table

The direct implementation (`TinyLexicalRetriever`) was evaluated against an independent functional reference calculation (`reference_lexical_oracle`) across identical inputs on the contract corpus:

| Query Input | Direct Retriever Results | Independent Oracle Results | Parity Verified? |
|---|---|---|---|
| `"red apple"` | `[A (score: 2), B (score: 1)]` | `[A (score: 2), B (score: 1)]` | **Identical** (`True`) ✓ |
| `"ocean"` | `[]` (0 matches) | `[]` (0 matches) | **Identical** (`True`) ✓ |
| `"apple"` | `[A (score: 1), B (score: 1)]` | `[A (score: 1), B (score: 1)]` | **Identical** (`True`) ✓ |
| `"blue"` | `[C (score: 1)]` | `[C (score: 1)]` | **Identical** (`True`) ✓ |
| `"sky red"` | `[A (score: 1), C (score: 1)]` | `[A (score: 1), C (score: 1)]` | **Identical** (`True`) ✓ |

**Observation**: Both approaches compute identical overlap scores, filter out zero-score documents, and resolve score ties deterministically by document ID.

---

## Deliberate Failure Verification

The test suite includes `test_deliberate_wrong_rank_order_fails` and `test_deliberate_wrong_empty_result_fails` verifying that:
- Any incorrect ranking order assertion (e.g. claiming B ranks before A) immediately raises `AssertionError`.
- Any non-empty expectation for unmatched query `"ocean"` immediately raises `AssertionError`.

## Test Run Summary

```
test_deliberate_wrong_empty_result_fails (test_example.TestDeliberateWrongAssertions.test_deliberate_wrong_empty_result_fails) ... ok
test_deliberate_wrong_rank_order_fails (test_example.TestDeliberateWrongAssertions.test_deliberate_wrong_rank_order_fails) ... ok
test_oracle_comparison_on_diverse_queries (test_example.TestFocusIndependentOracleComparison.test_oracle_comparison_on_diverse_queries) ... ok
test_oracle_comparison_query_ocean (test_example.TestFocusIndependentOracleComparison.test_oracle_comparison_query_ocean) ... ok
test_oracle_comparison_query_red_apple (test_example.TestFocusIndependentOracleComparison.test_oracle_comparison_query_red_apple) ... ok
test_case_insensitivity_and_punctuation_handling (test_example.TestLexicalRetrieverContract.test_case_insensitivity_and_punctuation_handling) ... ok
test_empty_query_returns_empty_results (test_example.TestLexicalRetrieverContract.test_empty_query_returns_empty_results) ... ok
test_invalid_document_inputs_raise_errors (test_example.TestLexicalRetrieverContract.test_invalid_document_inputs_raise_errors) ... ok
test_invalid_query_type_raises_type_error (test_example.TestLexicalRetrieverContract.test_invalid_query_type_raises_type_error) ... ok
test_query_ocean_returns_no_match (test_example.TestLexicalRetrieverContract.test_query_ocean_returns_no_match) ... ok
test_query_red_apple_ranks_a_before_b (test_example.TestLexicalRetrieverContract.test_query_red_apple_ranks_a_before_b) ... ok
test_tie_breaking_by_doc_id (test_example.TestLexicalRetrieverContract.test_tie_breaking_by_doc_id) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.001s

OK
```

## Simulation Disclaimers

| Aspect | Lexical Test Double (This Lab) | Production RAG Vector Search |
|---|---|---|
| Search Modality | Exact lowercase word-set overlap | Dense vector embeddings (cosine similarity) |
| Semantic Matching | None (lexical keyword exact match only) | Semantic similarity (e.g., synonyms, multi-lingual) |
| Index Structure | In-memory dictionary of Python sets | Approximate Nearest Neighbor graph (HNSW / FAISS) |
| Storage & Cloud | Local in-memory data structures | Azure AI Search / Cosmos DB Vector Store |
