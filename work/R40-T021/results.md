# R40-T021 — Test Results

## 1. Normal scenario

Command:

```bash
python3 04-prompt-engineering-fundamentals/applied-labs/r40-t021/example.py --name "Alice" --topic "Photosynthesis"
```

Actual output:

```json
{
  "rendered_prompt": "### INSTRUCTION\nYou are an AI educational tutor assisting students with customized study plans.\n\n### CONTEXT (USER DATA)\n- Student Name: Alice\n- Topic: Photosynthesis"
}
```

Exit code:

```text
0
```

**Result:** PASS — Successfully rendered declared variables with fixed instruction and delimiters.

---

## 2. Failure scenario (Missing required variable)

Command:

```bash
python3 04-prompt-engineering-fundamentals/applied-labs/r40-t021/example.py --name "Alice"
```

Actual output:

```text
ValueError: Missing required template variable(s): 'topic'
```

Exit code:

```text
1
```

**Result:** PASS — Missing variable `topic` is rejected with an informative error message and a nonzero exit code.

---

## 3. Boundary scenario (Literal braces in user data)

Command:

```bash
python3 04-prompt-engineering-fundamentals/applied-labs/r40-t021/example.py --name "Alice {student_id}" --topic "Sets: {x | x > 0}"
```

Actual output:

```json
{
  "rendered_prompt": "### INSTRUCTION\nYou are an AI educational tutor assisting students with customized study plans.\n\n### CONTEXT (USER DATA)\n- Student Name: Alice {student_id}\n- Topic: Sets: {x | x > 0}"
}
```

Exit code:

```text
0
```

**Result:** PASS — Curly braces contained inside user data remain literal and are not evaluated as template syntax.

---

## 4. Failure scenario (Unknown variable rejected)

Command:

```bash
python3 04-prompt-engineering-fundamentals/applied-labs/r40-t021/example.py --data '{"name": "Alice", "topic": "Photosynthesis", "role": "admin"}'
```

Actual output:

```text
ValueError: Unknown variable(s) provided: 'role'
```

Exit code:

```text
1
```

**Result:** PASS — Undeclared variable `role` is rejected with a nonzero exit code.

---

## 5. Automated unit tests

Command:

```bash
python3 -m unittest discover -s 04-prompt-engineering-fundamentals/applied-labs/r40-t021 -p "test_*.py"
```

Actual output:

```text
..............
----------------------------------------------------------------------
Ran 14 tests in 0.081s

OK
```

Exit code:

```text
0
```

**Result:** PASS — All 14 unit and CLI tests passed.

---

## 6. Deliberate failure verification

Command:

```bash
PYTHONPATH=04-prompt-engineering-fundamentals/applied-labs/r40-t021 python3 -c "
from example import render_prompt
result = render_prompt({'name': 'Alice', 'topic': 'Photosynthesis'})
assert 'Wrong Text' in result, 'Deliberate test failure for assertion verification'
"
```

Actual output:

```text
Traceback (most recent call last):
  File "<string>", line 4, in <module>
    assert 'Wrong Text' in result, 'Deliberate test failure for assertion verification'
           ^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Deliberate test failure for assertion verification
```

Exit code:

```text
1
```

**Result:** PASS — A deliberate wrong assertion causes the process to fail with exit code 1.

---

## Summary

| Scenario | Result |
|---|---|
| Normal template rendering | PASS |
| Missing variable failure (`topic`) | PASS |
| Literal curly braces in user data | PASS |
| Unknown variable rejection (`role`) | PASS |
| Single-pass non-recursive interpolation | PASS |
| Boundary delimiter separation | PASS |
| Automated unit tests (14 tests) | PASS |
| Deliberate failure verification | PASS |

All recorded checks completed successfully.
