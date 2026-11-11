"""Unit tests for Lesson 20 local lexical retriever test double."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))

from example import (  # noqa: E402
    LEXICAL_TEST_DOUBLE_NOTE,
    SYNTHETIC_DOCUMENTS,
    make_lexical_retriever,
    run_retrieval,
)


class TestLexicalRetrieverTestDouble(unittest.TestCase):
    def test_normal_red_apple_ranks_a_before_b_and_excludes_c(self) -> None:
        adapter = make_lexical_retriever(SYNTHETIC_DOCUMENTS)
        outcome = run_retrieval("red apple", adapter)

        self.assertTrue(outcome["simulation"])
        self.assertEqual(outcome["test_double_note"], LEXICAL_TEST_DOUBLE_NOTE)
        self.assertEqual(outcome["doc_ids"], ["A", "B"])
        self.assertEqual(outcome["matched_count"], 2)
        self.assertEqual(outcome["results"][0]["score"], 2)
        self.assertEqual(outcome["results"][1]["score"], 1)

    def test_normal_ocean_returns_no_match(self) -> None:
        adapter = make_lexical_retriever(SYNTHETIC_DOCUMENTS)
        outcome = run_retrieval("ocean", adapter)

        self.assertEqual(outcome["doc_ids"], [])
        self.assertEqual(outcome["results"], [])
        self.assertEqual(outcome["matched_count"], 0)

    def test_boundary_lowercase_normalization_and_doc_id_tie_break(self) -> None:
        reversed_docs = list(reversed(SYNTHETIC_DOCUMENTS))
        adapter = make_lexical_retriever(reversed_docs)
        outcome = run_retrieval("  APPLE  ", adapter)

        self.assertEqual(outcome["normalized_terms"], ["apple"])
        self.assertEqual(outcome["doc_ids"], ["A", "B"])
        self.assertEqual(outcome["results"][0]["score"], 1)
        self.assertEqual(outcome["results"][1]["score"], 1)

    def test_boundary_empty_and_whitespace_queries_return_no_match(self) -> None:
        adapter = make_lexical_retriever(SYNTHETIC_DOCUMENTS)
        for query in ("", "   \t\n"):
            outcome = run_retrieval(query, adapter)
            self.assertEqual(outcome["doc_ids"], [])
            self.assertEqual(outcome["results"], [])

    def test_callable_interface_accepts_custom_adapter(self) -> None:
        calls: list[str] = []

        def fake_adapter(query: str) -> list[dict[str, object]]:
            calls.append(query)
            return [{"doc_id": "Z", "text": "custom hit", "score": 99, "matched_terms": ["custom"]}]

        outcome = run_retrieval("custom", fake_adapter)
        self.assertEqual(calls, ["custom"])
        self.assertEqual(outcome["doc_ids"], ["Z"])
        self.assertEqual(outcome["matched_count"], 1)

    def test_failure_invalid_inputs_raise_value_error(self) -> None:
        adapter = make_lexical_retriever(SYNTHETIC_DOCUMENTS)
        with self.assertRaises(ValueError):
            run_retrieval(123, adapter)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            make_lexical_retriever([{"doc_id": "", "text": "invalid"}])
        with self.assertRaises(ValueError):
            make_lexical_retriever([{"doc_id": "A", "text": 42}])  # type: ignore[list-item]

    def test_fresh_process_cli_normal_and_invalid_flag(self) -> None:
        script = LAB_DIR / "example.py"

        ok_proc = subprocess.run(
            [sys.executable, str(script), "--query", "red apple"],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(ok_proc.stdout)
        self.assertTrue(payload["simulation"])
        self.assertEqual(payload["doc_ids"], ["A", "B"])

        empty_proc = subprocess.run(
            [sys.executable, str(script), "--query", "ocean"],
            capture_output=True,
            text=True,
            check=True,
        )
        empty_payload = json.loads(empty_proc.stdout)
        self.assertEqual(empty_payload["doc_ids"], [])

        bad_proc = subprocess.run(
            [sys.executable, str(script), "--unknown-flag"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(bad_proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
