# Applied Lab R40-T032: Token Budget Preflight & Recovery

## Overview
This applied lab implements a deterministic whitespace-token preflight validator with explicit truncation reporting and error recovery for Lesson 02 ("Exploring and comparing different LLMs").

## Lesson Concept Illustrated
Understanding token budgets, context window constraints, and pre-call request validation:
- When a prompt exceeds a designated token budget, the preflight processor truncates tokens deterministically and reports the exact count of removed tokens.
- Invalid configurations (such as negative budgets) or missing data (such as `None` prompts) are caught and reported with clear error messages.
- The preflight engine demonstrates recovery upon receiving the next valid prompt.

## Scope & Limitations
- **Tokenization**: Uses a whitespace splitting teaching approximation. It is not a real BPE or subword tokenizer (like tiktoken or SentencePiece).
- **Environment**: Pure Python 3 standard library; no external packages or GPU hardware required.

## Example Behavior
- **Budget 3 with `"one two three four"`**: retains `["one", "two", "three"]`, reports 1 removed token, `is_truncated = True`.
- **Empty input `""`**: retains `[]`, reports 0 removed tokens, `is_truncated = False`.
- **Negative budget `-1`**: raises `ValueError`.

## Execution
Run unit tests:
```bash
python3 -m unittest discover -s 02-exploring-and-comparing-different-llms/applied-labs/r40-t032 -p "test_*.py" -v
```
