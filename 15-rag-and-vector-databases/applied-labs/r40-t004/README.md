# Applied Lab R40-T004: Lexical Retriever with State Trace & Invariants

## Overview

This lab extends [Lesson 15: Retrieval Augmented Generation (RAG) and Vector Databases](../../README.md) by implementing a transparent lexical retriever that logs intermediate execution states and validates mathematical invariants linking those states to the final ranking.

## Contract & Multi-Stage State Trace

The retrieval pipeline executes in 5 discrete stages:
1. **Query Tokenization (`STEP 1`)**: Extracts lowercase word tokens from user query.
2. **Candidate Scoring (`STEP 2`)**: Calculates word set intersection count for each corpus document (`A="red apple"`, `B="green apple"`, `C="blue sky"`).
3. **Threshold Filtering (`STEP 3`)**: Prunes candidates with score < 1.
4. **Rank Ordering (`STEP 4`)**: Orders candidates by score descending, breaking ties by document ID ascending.
5. **Attribution Projection (`STEP 5`)**: Assembles `SearchResult` objects containing citations, scores, and matched tokens.

### Invariants Linking State to Output

- **Invariant I1 (Scoring Fidelity)**: Every output result's score equals the intermediate raw score from Step 2.
- **Invariant I2 (Monotonic Order)**: Results are strictly ordered by `(-score, doc_id)`.
- **Invariant I3 (Zero Pruning)**: Zero-score candidates never appear in the final output.

## Scope Note (Simulation / Test Double)

This component is an offline lexical retrieval test double using only Python's standard library. It requires zero cloud credentials, external model downloads, or GPU hardware.

## Invocations & Scenarios

Run the scenarios from repository root:

```bash
# Normal query (red apple -> A before B)
python3 15-rag-and-vector-databases/applied-labs/r40-t004/example.py --scenario normal

# Zero-match query (ocean -> [])
python3 15-rag-and-vector-databases/applied-labs/r40-t004/example.py --scenario zero_match

# Tie query (apple -> tie broken by doc_id)
python3 15-rag-and-vector-databases/applied-labs/r40-t004/example.py --scenario tie

# Inspect intermediate execution trace
python3 15-rag-and-vector-databases/applied-labs/r40-t004/example.py --trace "red apple"

# Canonical check
python3 15-rag-and-vector-databases/applied-labs/r40-t004/example.py --check

# Automated unit tests
python3 -m unittest discover -s 15-rag-and-vector-databases/applied-labs/r40-t004 -p "test_*.py" -v
```
