# R40-T050 Check Evidence

## Tool Versions

- Python: 3.15.2 (verified via `python3 --version`)
- unittest: Standard library (no external packages or virtual environments needed)

## Inputs, Expected vs Actual Results

### Fixture Documents
- Document A: `"red apple"`
- Document B: `"green apple"`
- Document C: `"blue sky"`

### Scenario 1 — Normal Scenario: Query `"red apple"`

| Field | Input / Query | Expected Result | Actual Result |
|---|---|---|---|
| **Query** | `"red apple"` | Overlap score ranking | Evaluated ✓ |
| **Ranked Document IDs** | N/A | `["A", "B"]` | `["A", "B"]` ✓ |
| **First Ranked Score** | Doc A | `score=2` | `score=2` ✓ |
| **Second Ranked Score** | Doc B | `score=1` | `score=1` ✓ |
| **Doc C Included?** | Doc C (score 0) | Excluded (`False`) | Excluded ✓ |

### Scenario 2 — Failure / Empty Scenario: Query `"ocean"`

| Field | Input / Query | Expected Result | Actual Result |
|---|---|---|---|
| **Query** | `"ocean"` | No matching documents | `[]` (Empty) ✓ |
| **Matches Count** | N/A | `0` | `0` ✓ |

### Focus: Three Applied Questions & Executable Checks

| Question | Type | Factual Answer | Executable Check | Result |
|---|---|---|---|---|
| **Q1** | Predict Output | `['A', 'B']` | Query `'apple'` scores 1 for both A and B; document ID tie-break sorts A before B. | Verified ✓ |
| **Q2** | Diagnose Failure | Tokenization mismatch: `'apple!'` != `'apple'` | Unnormalized `.split()` yields overlap 0; regex word tokenizer yields overlap 1. | Verified ✓ |
| **Q3** | Boundary Policy | Short-circuit and refuse generation | When query returns empty (e.g. `'ocean'`), RAG pipeline returns refusal rather than calling LLM. | Verified ✓ |

### Deliberate Failure Verification

The test suite includes `test_deliberate_wrong_ranking_fails` and `test_deliberate_wrong_ocean_match_fails` verifying that:
- Inverting the ranking order (`["B", "A"]`) fails with `AssertionError`.
- Asserting a non-empty match for `"ocean"` fails with `AssertionError`.

## Test Run Summary

```
Ran 12 tests in 0.001s
OK
Exit code: 0
```

## Simulation Disclaimers

| Simulation Property | Lexical Test Double | Production Vector Search (e.g. Azure AI Search) |
|---|---|---|
| Matching type | Exact lowercase word set overlap | Semantic dense vector embeddings (e.g. text-embedding-3) |
| Similarity metric | Integer set intersection count | Cosine similarity / inner product |
| Synonyms & Polysemy | Not recognized (literal match only) | Embedding space proximity captures semantic similarity |
| External infrastructure | None (pure in-memory Python) | Azure AI Search / Cosmos DB vector index |
