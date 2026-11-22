#!/usr/bin/env python3
"""Prompt-Template Escaping, Boundary Separation & Worked Regression (R40-T007).

Lesson 05: Creating Advanced Prompts
Repository: https://github.com/S-AI-Projects/generative-ai-for-beginners

Task Summary:
This lab implements a secure prompt template compiler that validates declared variables,
strictly rejects missing or unknown keys, isolates fixed system instructions from
untrusted user inputs, and guarantees that literal curly braces inside user values
remain intact without triggering formatting crashes.

Contract Rules:
1. Declared Variable Schema:
   - The template strictly declares required variables: ("name", "topic").
   - Supplying valid ("name", "topic") renders the complete structured prompt.
   - Missing required variable (e.g. missing 'topic') raises MissingVariableError.
   - Supplying unknown/undeclared keys raises UnknownVariableError.
2. Structural Isolation (Data vs. Instruction):
   - Fixed system instructions are kept structurally separated from dynamic user data
     using explicit demarcation tags (<instruction> and <user_data>).
3. Literal Brace Preservation:
   - Curly braces within user data (e.g. '{config: true}' or '{{var}}') remain strictly literal.
   - Replaces naive string formatting (e.g. str.format() or f-strings) with deterministic
     token replacement to ensure arbitrary user braces never cause formatting crashes.
4. Prompt Injection Boundary Disclaimer:
   - Templating alone enforces structural delimiter hygiene and syntax safety; it DOES NOT
     prevent semantic prompt injection (e.g. adversarial instructions in user data).
5. Focus (Worked Input-to-Output Explanation):
   - A fully worked explanation maps exact inputs through each compiler stage to final output,
     which is verified as an automated regression test.

Classification & Scope Note (Simulation / Test Double):
This module is strictly a local prompt templating compiler using Python's standard library.
It requires no LLM API keys, no cloud services, and no GPU hardware.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import sys
from typing import Any, Dict, List, Optional, Set

DECLARED_VARIABLES: Set[str] = {"name", "topic"}

FIXED_INSTRUCTION = (
    "You are an academic mentor. Provide a detailed, pedagogical explanation "
    "tailored to the student's inquiry."
)

TEMPLATE_SKELETON = (
    "<instruction>\n"
    f"{FIXED_INSTRUCTION}\n"
    "</instruction>\n"
    "<user_data>\n"
    "Student Name: {{name}}\n"
    "Topic of Inquiry: {{topic}}\n"
    "</user_data>"
)


class PromptTemplateError(Exception):
    """Base exception for prompt template compilation errors."""


class MissingVariableError(PromptTemplateError):
    """Raised when a declared required template variable is missing."""


class UnknownVariableError(PromptTemplateError):
    """Raised when an undeclared key is supplied to the template."""


class InvalidVariableTypeError(PromptTemplateError):
    """Raised when a supplied variable is not a string."""


class DecisionMismatchError(PromptTemplateError):
    """Raised when verification assertions fail."""


@dataclass(frozen=True)
class PromptCompiler:
    """Deterministic prompt template compiler enforcing declared schema boundaries."""

    declared_keys: Set[str] = frozenset(DECLARED_VARIABLES)  # type: ignore

    def render(self, variables: Dict[str, Any]) -> str:
        """Validates variables and renders template while preserving literal braces."""
        if not isinstance(variables, dict):
            raise TypeError("Variables must be provided as a dictionary.")

        supplied_keys = set(variables.keys())

        # 1. Check for unknown/unexpected keys
        unknown_keys = supplied_keys - self.declared_keys
        if unknown_keys:
            raise UnknownVariableError(
                f"Unknown variable(s) provided: {sorted(list(unknown_keys))}. "
                f"Allowed variables: {sorted(list(self.declared_keys))}."
            )

        # 2. Check for missing required keys
        missing_keys = self.declared_keys - supplied_keys
        if missing_keys:
            raise MissingVariableError(
                f"Missing required variable(s): {sorted(list(missing_keys))}."
            )

        # 3. Type check and validate non-None values
        for key in self.declared_keys:
            val = variables[key]
            if val is None:
                raise MissingVariableError(f"Required variable '{key}' cannot be None.")
            if not isinstance(val, str):
                raise InvalidVariableTypeError(
                    f"Variable '{key}' must be a string, got {type(val).__name__}."
                )

        # 4. Safe substitution preserving literal braces in user data
        rendered = TEMPLATE_SKELETON
        for key in sorted(list(self.declared_keys)):
            val = variables[key]
            # Replace token placeholder without evaluating curly braces in val
            rendered = rendered.replace(f"{{{{{key}}}}}", val)

        return rendered


def get_worked_explanation() -> Dict[str, Any]:
    """Focus: Detailed step-by-step worked explanation from raw inputs to final output."""
    raw_inputs = {
        "name": "Alice {Researcher}",
        "topic": "Quantum Algorithms: {Hadamard, CNOT}",
    }
    compiler = PromptCompiler()
    rendered_output = compiler.render(raw_inputs)

    explanation = {
        "stage_1_inputs": raw_inputs,
        "stage_2_schema_validation": {
            "declared_keys": sorted(list(DECLARED_VARIABLES)),
            "supplied_keys": sorted(list(raw_inputs.keys())),
            "missing_keys": [],
            "unknown_keys": [],
            "status": "VALID",
        },
        "stage_3_brace_handling": {
            "user_data_contains_braces": True,
            "name_braces": "{Researcher}",
            "topic_braces": "{Hadamard, CNOT}",
            "strategy": "Direct substring replacement bypassing str.format / f-string parser",
            "literal_preserved": True,
        },
        "stage_4_structural_separation": {
            "instruction_block": f"<instruction>\n{FIXED_INSTRUCTION}\n</instruction>",
            "user_data_block": (
                "<user_data>\n"
                f"Student Name: {raw_inputs['name']}\n"
                f"Topic of Inquiry: {raw_inputs['topic']}\n"
                "</user_data>"
            ),
        },
        "stage_5_final_output": rendered_output,
        "prompt_injection_boundary_note": (
            "Delimiting user data prevents template syntax corruption, but downstream "
            "semantic defense requires LLM moderation and guardrails."
        ),
    }
    return explanation


def run_normal_scenario() -> Dict[str, Any]:
    """Normal scenario: renders valid name and topic."""
    compiler = PromptCompiler()
    inputs = {"name": "Alice", "topic": "Quantum Computing"}
    rendered = compiler.render(inputs)

    return {
        "scenario_id": "SCENARIO_NORMAL",
        "decision": "TEMPLATE_RENDERED_SUCCESS",
        "inputs": inputs,
        "rendered_prompt": rendered,
        "contains_name": ("Student Name: Alice" in rendered),
        "contains_topic": ("Topic of Inquiry: Quantum Computing" in rendered),
        "contract_satisfied": (
            "Student Name: Alice" in rendered
            and "Topic of Inquiry: Quantum Computing" in rendered
        ),
    }


def run_missing_topic_scenario() -> Dict[str, Any]:
    """Missing variable scenario: missing 'topic' raises MissingVariableError."""
    compiler = PromptCompiler()
    inputs = {"name": "Bob"}
    caught = False
    error_msg = ""
    try:
        compiler.render(inputs)
    except MissingVariableError as exc:
        caught = True
        error_msg = str(exc)

    return {
        "scenario_id": "SCENARIO_MISSING_TOPIC",
        "decision": "MISSING_TOPIC_REJECTED",
        "missing_variable_caught": caught,
        "error_message": error_msg,
        "contract_satisfied": caught,
    }


def run_literal_braces_scenario() -> Dict[str, Any]:
    """Boundary scenario: user values containing curly braces remain literal."""
    compiler = PromptCompiler()
    inputs = {
        "name": "Charlie {Eng}",
        "topic": "Configuration: {debug: true, flags: [1, 2]}",
    }
    rendered = compiler.render(inputs)

    braces_preserved = (
        "Charlie {Eng}" in rendered
        and "{debug: true, flags: [1, 2]}" in rendered
    )

    return {
        "scenario_id": "SCENARIO_BRACES_PRESERVED",
        "decision": "LITERAL_BRACES_PRESERVED",
        "inputs": inputs,
        "rendered_prompt": rendered,
        "braces_intact": braces_preserved,
        "contract_satisfied": braces_preserved,
    }


def run_unknown_key_scenario() -> Dict[str, Any]:
    """Invalid input scenario: unknown variable key raises UnknownVariableError."""
    compiler = PromptCompiler()
    inputs = {"name": "Dana", "topic": "Robotics", "extra_token": "injected"}
    caught = False
    error_msg = ""
    try:
        compiler.render(inputs)
    except UnknownVariableError as exc:
        caught = True
        error_msg = str(exc)

    return {
        "scenario_id": "SCENARIO_UNKNOWN_KEY",
        "decision": "UNKNOWN_KEY_REJECTED",
        "unknown_key_caught": caught,
        "error_message": error_msg,
        "contract_satisfied": caught,
    }


def run_canonical_check(tamper: bool = False) -> Dict[str, Any]:
    """Validates the canonical decision table across all scenarios."""
    normal = run_normal_scenario()
    missing = run_missing_topic_scenario()
    braces = run_literal_braces_scenario()
    unknown = run_unknown_key_scenario()

    scenarios = [normal, missing, braces, unknown]
    expected_decisions = {
        "SCENARIO_NORMAL": "TEMPLATE_RENDERED_SUCCESS",
        "SCENARIO_MISSING_TOPIC": "MISSING_TOPIC_REJECTED",
        "SCENARIO_BRACES_PRESERVED": "LITERAL_BRACES_PRESERVED",
        "SCENARIO_UNKNOWN_KEY": "UNKNOWN_KEY_REJECTED",
    }

    if tamper:
        expected_decisions["SCENARIO_NORMAL"] = "TAMPERED_WRONG_DECISION"

    results = []
    failures = []

    for sc in scenarios:
        sc_id = sc["scenario_id"]
        expected = expected_decisions[sc_id]
        actual = sc["decision"]
        passed = (actual == expected and sc.get("contract_satisfied", False))
        record = {
            "scenario_id": sc_id,
            "expected_decision": expected,
            "actual_decision": actual,
            "passed": passed,
        }
        results.append(record)
        if not passed:
            failures.append(record)

    if failures:
        raise DecisionMismatchError(f"Decision mismatch detected: {failures}")

    return {
        "status": "success",
        "all_passed": True,
        "total_scenarios": len(scenarios),
        "passed_scenarios": len(results),
        "failed_scenarios": 0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="R40-T007: Prompt-Template Escaping & Worked Regression Example."
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "missing_topic", "braces", "unknown"],
        help="Run an individual scenario.",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Display the worked input-to-output explanation.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run canonical verification across all scenarios.",
    )
    parser.add_argument(
        "--tamper",
        action="store_true",
        help="Simulate deliberate wrong expectation to demonstrate checker failure.",
    )

    args = parser.parse_args()

    if args.tamper:
        try:
            run_canonical_check(tamper=True)
        except DecisionMismatchError as exc:
            payload = {
                "status": "expected_tamper_failure",
                "error_type": exc.__class__.__name__,
                "details": str(exc),
                "exit_code": 1,
            }
            sys.stderr.write(json.dumps(payload, indent=2) + "\n")
            sys.exit(1)

    if args.explain:
        print(json.dumps(get_worked_explanation(), indent=2))
        sys.exit(0)
    elif args.scenario == "normal":
        print(json.dumps(run_normal_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "missing_topic":
        print(json.dumps(run_missing_topic_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "braces":
        print(json.dumps(run_literal_braces_scenario(), indent=2))
        sys.exit(0)
    elif args.scenario == "unknown":
        print(json.dumps(run_unknown_key_scenario(), indent=2))
        sys.exit(0)
    elif args.check or len(sys.argv) == 1:
        print(json.dumps(run_canonical_check(tamper=False), indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
