# R40-T038 Check Evidence

## Tool Versions

- Python: 3.14.6 (verified via `python3 --version`)
- unittest: Standard library (no external packages or virtual environments needed)

## Inputs, Expected vs Actual Results

### Scenario 1 — Normal Scenario: Contract Fixture `query="red"`

Corpus:
- `doc_1`: `"red apple"`
- `doc_2`: `"red berry"`
- `doc_3`: `"blue sky"`

| Field | Input Parameter | Expected Output | Actual Output |
|---|---|---|---|
| **Query** | `"red"` | N/A | Processed ✓ |
| **Default Threshold** | `min_score=1` | N/A | Applied ✓ |
| **Result Count** | N/A | `2` (`doc_3` omitted) | `2` ✓ |
| **Rank 1 Document** | N/A | `doc_id="doc_1"`, `score=1` | `doc_id="doc_1"`, `score=1` ✓ |
| **Rank 2 Document** | N/A | `doc_id="doc_2"`, `score=1` | `doc_id="doc_2"`, `score=1` ✓ |
| **Tie-Breaker Order** | N/A | `doc_1` before `doc_2` (stable ID order) | `doc_1` before `doc_2` ✓ |
| **Zero-Score Omission** | N/A | `doc_3` omitted (score = 0 < 1) | `doc_3` omitted ✓ |

### Scenario 2 — Score Differentiation: `query="red apple"`

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Query** | `"red apple"` | `doc_1` scores 2, `doc_2` scores 1 | `doc_1` scores 2, `doc_2` scores 1 ✓ |
| **Ranked Order** | N/A | `["doc_1", "doc_2"]` | `["doc_1", "doc_2"]` ✓ |

### Scenario 3 — Smallest Valid Case

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Corpus** | `{"min_1": "a"}` | 1 document, single character | Processed ✓ |
| **Query** | `"a"` | Single token query | Processed ✓ |
| **Result** | N/A | `[SearchResult(doc_id="min_1", score=1, text="a")]` | Verified ✓ |

### Scenario 4 — Failure Scenarios

| Field | Input Parameter | Expected Result | Actual Result |
|---|---|---|---|
| **Negative Threshold** | `min_score=-1` | `ValueError` raised | `ValueError` raised ✓ |
| **Non-string Query** | `12345` | `TypeError` raised | `TypeError` raised ✓ |
| **Empty Document ID** | `""` | `ValueError` raised | `ValueError` raised ✓ |
| **Non-string Content** | `999` | `TypeError` raised | `TypeError` raised ✓ |

---

## Focus: Smallest Valid, Boundary, and Invalid Cases & Exact Boundary Decision

| Category | Description | Input / Threshold | Expected Status | Exact Boundary Decision Rule |
|---|---|---|---|---|
| **Smallest Valid** | Single character doc and query | `doc="a"`, `query="a"` | Included with `score=1` | `score >= 1` satisfied on minimal 1-character token. |
| **Threshold Boundary (Exact)** | Score equals threshold | `score=1`, `min_score=1` | Included (`doc_1`, `doc_2`) | `score >= min_score` is inclusive; boundary point is retained. |
| **Threshold Boundary (Excluded)** | Score below threshold | `score=0`, `min_score=1` | Omitted (`doc_3`) | `score < min_score` causes document to be dropped from results. |
| **Tie-Breaking Boundary** | Identical score tie | `score=1` vs `score=1` | Stable: `doc_1` before `doc_2` | Deterministic tie-breaker: alphabetical comparison on `doc_id`. |
| **Empty Query Boundary** | Empty/whitespace string | `query="   "` | `[]` (0 matches) | Zero tokens match zero documents. |
| **Invalid Threshold** | Negative threshold | `min_score=-1` | `ValueError` raised | Thresholds must be non-negative integers (`threshold >= 0`). |

**Exact Boundary Decision Rationale**:
1. **Inclusion Condition (`score >= min_score`)**:
   We choose an inclusive boundary. Setting `min_score=1` by default guarantees that documents with at least one matching token are passed to downstream generation steps, while completely ungrounded documents (score = 0) are omitted.
2. **Deterministic Sort Key (`(-score, doc_id)`)**:
   Primary descending sort on score ranks the most relevant matches first. Secondary ascending sort on `doc_id` guarantees consistent, reproducible rankings across executions when scores tie.

---

## Deliberate Failure Verification

The test suite includes `test_deliberate_wrong_tie_order_assertion_fails` and `test_deliberate_wrong_omission_assertion_fails` verifying that:
- Any incorrect tie-break order assertion (e.g. claiming `doc_2` ranks before `doc_1`) immediately raises `AssertionError`.
- Any unexpected inclusion of omitted zero-score documents (e.g. `doc_3` for query `"red"`) immediately raises `AssertionError`.

## Test Run Summary

```
test_boundary_case_matrix_audit (test_example.TestBoundaryCasesAndSmallestValid.test_boundary_case_matrix_audit) ... ok
test_boundary_zero_min_score_includes_zero_score_documents (test_example.TestBoundaryCasesAndSmallestValid.test_boundary_zero_min_score_includes_zero_score_documents) ... ok
test_empty_and_whitespace_query_boundary (test_example.TestBoundaryCasesAndSmallestValid.test_empty_and_whitespace_query_boundary) ... ok
test_smallest_valid_case (test_example.TestBoundaryCasesAndSmallestValid.test_smallest_valid_case) ... ok
test_threshold_boundary_exact_match (test_example.TestBoundaryCasesAndSmallestValid.test_threshold_boundary_exact_match) ... ok
test_deliberate_wrong_omission_assertion_fails (test_example.TestDeliberateWrongAssertions.test_deliberate_wrong_omission_assertion_fails) ... ok
test_deliberate_wrong_tie_order_assertion_fails (test_example.TestDeliberateWrongAssertions.test_deliberate_wrong_tie_order_assertion_fails) ... ok
test_invalid_doc_id_raises_value_error (test_example.TestInvalidCasesAndFailures.test_invalid_doc_id_raises_value_error) ... ok
test_invalid_doc_text_raises_type_error (test_example.TestInvalidCasesAndFailures.test_invalid_doc_text_raises_type_error) ... ok
test_invalid_query_type_raises_type_error (test_example.TestInvalidCasesAndFailures.test_invalid_query_type_raises_type_error) ... ok
test_negative_threshold_raises_value_error (test_example.TestInvalidCasesAndFailures.test_negative_threshold_raises_value_error) ... ok
test_query_red_matches_apple_and_berry_equally_with_stable_tie_break (test_example.TestRankedSearchContract.test_query_red_matches_apple_and_berry_equally_with_stable_tie_break) ... ok
test_score_ranking_differentiation (test_example.TestRankedSearchContract.test_score_ranking_differentiation) ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
```

## Simulation Disclaimers

| Aspect | Local Ranked Search Engine (This Lab) | Production Cloud Search Application |
|---|---|---|
| Search Index | In-memory token set dictionary | Azure AI Search vector/hybrid index |
| Scoring Model | Discrete word overlap count | Cosine similarity on dense embeddings (`text-embedding-ada-002`) |
| Hardware / Resources | Local CPU, Python 3 stdlib only | Dedicated Azure cloud search tier |
| Semantic Matching | Exact keyword matching only | Semantic synonym and semantic re-ranking |
