# Check Evidence for Task R40-T040

## Task Information
- **Student**: Vedant Kakde
- **Task ID**: R40-T040
- **Working Branch**: `student/e26b07f0772/R40-T040`
- **Topic**: 16-open-source-models (Model Selection Assessment & Applied Questions)

## Acceptance Criteria Fulfilled
1. Normal, boundary, and missing-information scenarios each have an explicit expected decision and rationale tied to Lesson 16.
2. The checker fails when a decision in the published table is altered.
3. Three applied questions (predict output, diagnose failure, choose boundary policy) are implemented with rationales and executable automated checks.
4. Local execution runs purely offline with zero external model weights or cloud API calls.

## Test Execution Command
```bash
python3 -m unittest discover -s 16-open-source-models/applied-labs/r40-t040 -p "test_*.py" -v
```
