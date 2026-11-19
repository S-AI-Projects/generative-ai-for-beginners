# Applied Lab (R40-T026): Lexical Retriever with Source Attribution and Equivalence Refactoring

This hands-on applied lab extends Lesson 20 (**Building with Mistral Models**) with a local contract fixture modeling lexical retrieval, source attribution, deterministic tie-breaking, and before/after equivalence refactoring.

---

## 1. Context & Lesson Connection

In Lesson 20 ([Building with Mistral Models](../../README.md#rag-example-using-mistral-large-2)), the curriculum demonstrates how to implement a Retrieval-Augmented Generation (RAG) architecture using Mistral Large 2, an external multilingual embedding model (`cohere-embed-v3-multilingual`), and a FAISS vector index.

In the lesson's RAG example:
- Chunks of text are retrieved based on nearest-neighbor Euclidean distance in vector space.
- The retrieved chunks are injected as an unannotated list of strings into the Mistral prompt context:
  ```python
  prompt = f"""
  Context information is below.
  ---------------------
  {retrieved_chunks}
  ---------------------
  Given the context information and not prior knowledge, answer the query.
  Query: {question}
  Answer:
  """
  ```
- **Where the lesson needs extension:**
  1. **Source Attribution:** Chunks in the lesson lack document identifiers or provenance metadata. In enterprise RAG, answers must cite source documents (e.g. `[Source A]`, `[Doc 42]`) for auditing, verification, and grounded generation.
  2. **Query Normalization:** Query terms must be normalized (lowercased, stripped of punctuation and irregular whitespace) to prevent trivial lexical mismatch.
  3. **Deterministic Ranking and Tie-Breaking:** When multiple documents exhibit identical relevance, ordering must be stable and deterministic (e.g. breaking ties by document ID) rather than dependent on arbitrary vector index order.
  4. **Boundary Handling & Empty Results:** Vector search always returns the $k$ nearest neighbors regardless of distance. When a query is completely unrelated to the corpus (e.g. asking about "ocean" against fruit and sky documents), dense vector search returns irrelevant chunks that can cause hallucinations. A well-behaved retriever must enforce a relevance threshold and return an empty result set (`[]`) when no match exists.

---

## 2. Classification & Scope Note: Lexical Test Double

> **Explicit Educational Classification:**
> This component is strictly a **lexical test double**, not a production vector search.
>
> - **Zero Cloud / Hardware Requirements:** Runs entirely with Python's standard library (`re`, `json`, `argparse`, `dataclasses`, `unittest`). No API keys, paid cloud endpoints, local LLM weight downloads, or GPU/hardware accelerators are required.
> - **Simplification Boundaries:**
>   - **Lexical Overlap vs. Dense Vector Embeddings:** Computes exact word-set intersections (`len(query_words & doc_words)`), not semantic latent vectors. It does not generalize to synonyms (e.g. "crimson" will not match "red").
>   - **Unweighted Term Overlap vs. BM25 / TF-IDF:** All matching tokens contribute equally with weight 1 (no inverse document frequency scaling).
>   - **In-Memory Fixture vs. Persistent Vector Store:** Operates over a tiny in-memory tuple of local documents rather than distributed indices like FAISS, Pinecone, or Azure AI Search.
>   - **Purpose:** Serves as a deterministic, instantaneous unit-test double to verify retrieval contracts, source attribution formatting, ranking pipelines, and refactoring invariants without network flakiness or external cost.

---

## 3. Contribution Focus: Baseline Implementation and Responsibility Extraction

This lab demonstrates the core refactoring focus:
> **"Implement a correct baseline, then extract one named responsibility. Keep the same contract and prove before/after equivalence on the fixture."**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Monolithic Baseline: BaselineLexicalRetriever                            │
│    - Tokenizes query and documents inline                                  │
│    - Computes word-set intersection directly                               │
│    - Filters score == 0                                                    │
│    - Sorts by (-score, doc_id)                                             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                               Refactor│ Extract Named Responsibility:
                                       │ `WordSetOverlapScorer`
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. Extracted Responsibility: WordSetOverlapScorer                          │
│    - tokenize(text: str) -> Set[str]                                        │
│    - score_tokens(query_tokens, doc_tokens) -> int                          │
│    - score(query, doc_text) -> int                                          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Composed Into
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. Refactored Component: RefactoredLexicalRetriever                         │
│    - Same Public Contract: retrieve(query: str) -> List[SearchResult]       │
│    - Pre-indexes tokenized corpus using WordSetOverlapScorer                │
│    - Applies deterministic tie-breaking: (-score, doc_id)                   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. Equivalence Prover: prove_before_after_equivalence()                     │
│    - Asserts 100% parity across doc_ids, scores, counts, and rank order     │
│    - Catches deliberate mutations / regressions via EquivalenceMismatchError│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. The Canonical Fixture & Published Decision Table

The local corpus fixture consists of three documents:
- **Doc A:** `"red apple"`
- **Doc B:** `"green apple"`
- **Doc C:** `"blue sky"`

| Scenario ID | Scenario Type | Query | Expected Decision | Expected Output Document IDs & Scores | Educational Rationale Highlight |
|---|---|---|---|---|---|
| `SCENARIO_NORMAL` | **Normal** | `"red apple"` | `RETRIEVAL_SUCCESS_RANKED` | `["A", "B"]`<br>Scores: `[2, 1]` | Doc A matches 2 words (`{'red', 'apple'}`), Doc B matches 1 word (`{'apple'}`). Ranks A before B with source attribution; Doc C has 0 overlap and is omitted. |
| `SCENARIO_BOUNDARY` | **Boundary** | `"ocean"` | `EMPTY_RESULT_NO_MATCH` | `[]`<br>Scores: `[]` | Zero overlap with any document in corpus. Returns empty result set `[]`, preventing hallucinations in downstream LLM generation. |
| `SCENARIO_TIEBREAK` | **Boundary** | `"apple"` | `RETRIEVAL_TIEBREAK_RESOLVED` | `["A", "B"]`<br>Scores: `[1, 1]` | Both Doc A and Doc B match 1 word (`{'apple'}`). Ties are deterministically resolved by document ID in ascending order (`'A' < 'B'`). |
| `SCENARIO_EQUIVALENCE` | **Equivalence** | Test Suite (10 queries) | `REFACTORING_EQUIVALENCE_PROVEN` | Identical across all queries | Proves that `BaselineLexicalRetriever` and `RefactoredLexicalRetriever` (with `WordSetOverlapScorer`) satisfy the identical contract and rankings. |

---

## 5. Usage & CLI Invocations

Run all commands from the repository root:

### 1. Execute the Decision Table Checker across all Scenarios

```bash
python3 20-mistral/applied-labs/r40-t026/example.py --check
```

**Expected Output (`exit 0`):**
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

### 2. Execute Individual Scenarios

Normal Scenario ("red apple"):
```bash
python3 20-mistral/applied-labs/r40-t026/example.py --scenario normal
```

Boundary Scenario ("ocean"):
```bash
python3 20-mistral/applied-labs/r40-t026/example.py --scenario boundary
```

Tie-breaking Scenario ("apple"):
```bash
python3 20-mistral/applied-labs/r40-t026/example.py --scenario tiebreak
```

Equivalence Proof across full query suite:
```bash
python3 20-mistral/applied-labs/r40-t026/example.py --prove-equivalence
```

### 3. Verify Deliberate Tamper Failure Detection

To verify that deliberate mutation or tampering causes the checker to catch the discrepancy and exit with a non-zero exit code:

```bash
python3 20-mistral/applied-labs/r40-t026/example.py --tamper
```

**Expected Result (`exit 1`):**
```
[DEMO] Injecting deliberate tamper into SCENARIO_NORMAL expected decision...
[EXPECTED FAILURE CONFIRMED] Caught: Scenario 'SCENARIO_NORMAL' decision mismatch: expected 'DELIBERATELY_MUTATED_WRONG_DECISION', got 'RETRIEVAL_SUCCESS_RANKED'
```

### 4. Run the Automated Unit Test Suite

```bash
python3 -m unittest discover -s 20-mistral/applied-labs/r40-t026 -p "test_*.py"
```

All 30 unit tests pass in a fresh process, testing baseline functionality, extracted scorer logic, refactored composition, before/after equivalence proofs, tamper detection, prompt citation formatting, and subprocess CLI execution.
