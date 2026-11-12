# R40-T041 — Test Results

## 1. Normal search scenario

Command:

```bash
python3 08-building-search-applications/applied-labs/r40-t041/example.py red
```

Actual output:

```json
[
  {
    "id": 1,
    "score": 1
  },
  {
    "id": 2,
    "score": 1
  }
]
```

**Result:** PASS — Both matching documents were returned with equal scores and sorted by ascending ID.

## 2. No-match scenario

Command:

```bash
python3 08-building-search-applications/applied-labs/r40-t041/example.py orange
```

Actual output:

```json
[]
```

**Result:** PASS — No documents matched the query.

## 3. Minimum-score scenario

Command:

```bash
python3 08-building-search-applications/applied-labs/r40-t041/example.py red --min-score 2
```

Actual output:

```json
[]
```

**Result:** PASS — Results below the minimum score were excluded.

## 4. Automated unit tests

Command:

```bash
python3 -m unittest discover -s 08-building-search-applications/applied-labs/r40-t041 -p "test_*.py"
```

Actual output:

```text
.......
----------------------------------------------------------------------
Ran 7 tests in 0.000s

OK
```

**Result:** PASS — All 7 automated tests passed.

## Summary

| Scenario | Result |
|---|---|
| Normal search | PASS |
| No-match search | PASS |
| Minimum-score filtering | PASS |
| Automated tests | PASS |
| Boundary scenario | PASS |
| Failure scenario | PASS |

All recorded checks completed successfully.


## 5. Boundary scenario

Command:

```bash
python3 08-building-search-applications/applied-labs/r40-t041/example.py red --min-score 1
```

Actual output:

```json
[
  {
    "id": 1,
    "score": 1
  },
  {
    "id": 2,
    "score": 1
  }
]
```

**Result:** PASS — Results equal to the minimum score are included.

## 6. Failure scenario

Command:

```bash
python3 08-building-search-applications/applied-labs/r40-t041/example.py ""
```

Actual output:

```text
ValueError: Query must be a non-empty string.
```

Exit code:

```text
1
```

**Result:** PASS — Invalid input produces an error and a nonzero exit code.
