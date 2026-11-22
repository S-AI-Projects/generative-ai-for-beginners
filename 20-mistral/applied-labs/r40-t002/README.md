# Applied Lab R40-T002: Lexical Retriever with Source Attribution & Boundary Cases

## Overview

This lab extends [Lesson 20: Building with Mistral Models](../../README.md) by introducing a deterministic, source-attributed lexical retrieval test double.

In retrieval-augmented generation (RAG) architectures, foundation models rely on retrievers to supply relevant context from knowledge bases. Grounded citations require accurate source attribution (document IDs), deterministic ranking when scores tie, and safe handling of zero-overlap queries.

## Contract & Boundary Decision

1. **Document Corpus**:
   - `A`: `"red apple"`
   - `B`: `"green apple"`
   - `C`: `"blue sky"`
2. **Lexical Overlap Scoring**:
   - Computed as token intersection count: `|words(query) ∩ words(document)|`.
   - Case-insensitive, whitespace-normalized.
3. **Deterministic Tie-Breaking**:
   - Primary sort: score descending.
   - Secondary sort: document ID ascending (alphabetical).
   - E.g., for query `"apple"`, both A and B have score 1; A is ranked before B.
4. **Boundary Query `"ocean"`**:
   - Yields zero overlap across all corpus documents.
   - Returns an empty list (`[]`) to avoid injecting irrelevant noise into generation contexts.
5. **Smallest Valid & Invalid Cases**:
   - Smallest valid: Single matching word (e.g. `"sky"` -> `C`, score 1).
   - Invalid cases: Empty or whitespace-only queries raise `ValueError`; non-string inputs raise `TypeError`.

## Scope Note (Simulation / Test Double)

This component is an offline lexical retriever test double using only Python's standard library.
It is **not** a vector search or neural embedding engine. It requires zero cloud credentials, external model weights, or GPU acceleration.

## Invocations & Scenarios

Run the scenarios from the repository root:

```bash
# Normal query (red apple -> ranks A before B)
python3 20-mistral/applied-labs/r40-t002/example.py --scenario normal

# Zero-match boundary query (ocean -> [])
python3 20-mistral/applied-labs/r40-t002/example.py --scenario zero_match

# Tie-breaking query (apple -> A before B)
python3 20-mistral/applied-labs/r40-t002/example.py --scenario tie

# Canonical check
python3 20-mistral/applied-labs/r40-t002/example.py --check

# Automated unit tests
python3 -m unittest discover -s 20-mistral/applied-labs/r40-t002 -p "test_*.py" -v
```
