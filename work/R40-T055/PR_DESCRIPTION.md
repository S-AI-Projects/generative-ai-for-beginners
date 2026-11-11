# [Lesson 20] Add local lexical retriever test double (`R40-T055`)

## Summary

Extends "Building with Mistral Models" in `20-mistral/README.md` with a deterministic local lexical retriever test double (`20-mistral/applied-labs/r40-t055/example.py`) and unit tests (`20-mistral/applied-labs/r40-t055/test_example.py`).

- Isolates the external retrieval dependency behind a callable interface (`RetrieverFn = Callable[[str], list[dict[str, Any]]]`) and supplies a deterministic local adapter (`make_lexical_retriever`) over documents `A = "red apple"`, `B = "green apple"`, and `C = "blue sky"`.
- Scores lowercase word-set overlap and breaks ties ascending by `doc_id`, ranking `A` before `B` for `"red apple"` and returning `[]` for `"ocean"`.
- Explicitly labels the implementation as a **lexical test double, not a production vector search**, and documents which real-service behaviors (multilingual dense embeddings, FAISS indexing/L2 similarity, network/auth reliability, and Mistral answer synthesis) this mock does not establish.
- Uses Python 3.9+ standard library only (no model download, paid provider, GPU, or physical device).

## Checks & Verification

All verification runs and recorded inputs, expected vs. actual results, and tool versions are stored in `work/R40-T055/`:

- Verification harness: `work/R40-T055/run_checks.py`
- Recorded results & tool versions: `work/R40-T055/check-results.json`
- Commands executed in fresh processes:
  - `python3 20-mistral/applied-labs/r40-t055/example.py`
  - `python3 -m unittest discover -s 20-mistral/applied-labs/r40-t055 -p "test_*.py"` (`Ran 7 tests`, `OK`, exit code `0`)
  - `python3 work/R40-T055/run_checks.py` (5 targeted CLI scenarios + default run + 7 unit tests + deliberate wrong-result check confirming non-zero exit code `1` on `AssertionError`)

> **Note for upstreaming:** Remove `work/R40-T055/` on a later upstream branch before merging into upstream `main`.
