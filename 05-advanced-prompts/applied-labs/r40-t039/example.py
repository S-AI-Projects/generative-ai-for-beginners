"""
R40-T039 · Applied Lab: Prompt Template Validation and Data Boundary Separation
================================================================================

This module extends Lesson 05 ("Creating Advanced prompts") by implementing a
deterministic template rendering engine that enforces declared variable validation,
preserves literal braces in user data, and structurally isolates user data from
fixed instruction fields.

Lesson connection
-----------------
Lesson 05 explains how prompts are constructed using templates with variables
(e.g., {{variable}}) populated from external APIs or user input.
In production prompt engineering:
  1. Dynamic values must match declared variable contracts: missing keys or unknown
     keys must be rejected before sending the prompt to the model.
  2. Braces within user data (e.g., JSON strings, code blocks, or mathematical sets)
     must remain strictly literal and not trigger syntax errors, unescaped format
     string bugs, or template injection.
  3. User data must be kept distinct from fixed instruction fields through explicit
     structural boundaries (delimiters or envelopes) to prevent ambiguous instruction
     confusion.
  4. Templating alone does NOT prevent prompt injection: while strict templating
     guarantees syntactic isolation and data boundary integrity, downstream LLMs
     interpret text semantically, meaning semantic prompt injection (e.g., "Ignore
     previous instructions...") requires defense-in-depth (system-level guardrails,
     moderation, and post-filtering).

Simplification boundary
-----------------------
This local implementation operates purely as an in-memory string and template
validator. It does NOT:
  - Call remote LLM APIs (e.g., Azure OpenAI, OpenAI, Anthropic).
  - Download or run local neural weights.
  - Claim real-world model accuracy, alignment, or resistance to semantic jailbreaks.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


class TemplateValidationError(ValueError):
    """Base exception for template validation failures."""
    pass


class MissingVariableError(TemplateValidationError):
    """Raised when a required declared variable is missing from supplied inputs."""
    pass


class UnknownVariableError(TemplateValidationError):
    """Raised when undeclared keys are supplied to the template."""
    pass


class InvalidVariableTypeError(TemplateValidationError, TypeError):
    """Raised when a supplied variable is not of the expected string type."""
    pass


class DelimitationStyle(str, Enum):
    """
    Delimitation styles for separating fixed instruction fields from user data.

    RAW:
        Minimal labeled text blocks. Low overhead, basic human readability.
    TAGGED:
        Explicit XML-style boundary tags (<instruction> and <user_data>).
        Standard for frontier models to separate system instruction from user inputs.
    ENVELOPE:
        Structured JSON envelope separating system instructions and user data payload.
    """
    RAW = "raw"
    TAGGED = "tagged"
    ENVELOPE = "envelope"


@dataclass(frozen=True)
class RenderedPrompt:
    """
    Immutable result of rendering a validated prompt template.

    Attributes
    ----------
    instruction : str
        The fixed instruction field.
    declared_variables : tuple[str, ...]
        Declared variable names for the template.
    user_data : dict[str, str]
        Validated user data mapping.
    rendered_text : str
        The assembled prompt with structural boundaries.
    delimitation_style : str
        The boundary delimitation style used.
    contains_raw_literal_braces : bool
        Whether user data contained literal '{' or '}' characters.
    semantic_injection_prevented_by_templating_alone : bool
        Always False. Templating isolates structure, not semantic meaning.
    """
    instruction: str
    declared_variables: tuple[str, ...]
    user_data: dict[str, str]
    rendered_text: str
    delimitation_style: str
    contains_raw_literal_braces: bool
    semantic_injection_prevented_by_templating_alone: bool = False


class PromptTemplate:
    """
    Deterministic prompt template with strict variable contract and boundary isolation.

    Enforces:
      - All declared variables must be supplied (missing keys fail).
      - No extraneous keys may be supplied (unknown keys fail).
      - User data values must be strings.
      - Braces inside user data are preserved byte-for-byte as literal characters.
      - Fixed instruction fields are structurally isolated from user data.
    """

    def __init__(
        self,
        instruction: str,
        declared_variables: Sequence[str] = ("name", "topic"),
        delimitation_style: str | DelimitationStyle = DelimitationStyle.TAGGED,
    ) -> None:
        if not instruction or not isinstance(instruction, str):
            raise ValueError("Instruction must be a non-empty string.")

        self._instruction = instruction.strip()
        self._declared_variables = tuple(declared_variables)

        if isinstance(delimitation_style, str):
            self._delimitation_style = DelimitationStyle(delimitation_style.lower())
        else:
            self._delimitation_style = delimitation_style

    @property
    def instruction(self) -> str:
        return self._instruction

    @property
    def declared_variables(self) -> tuple[str, ...]:
        return self._declared_variables

    @property
    def delimitation_style(self) -> DelimitationStyle:
        return self._delimitation_style

    def validate_variables(self, variables: Mapping[str, Any]) -> dict[str, str]:
        """
        Validate input mapping against declared variables.

        Raises
        ------
        MissingVariableError
            If any declared variable is missing or None.
        UnknownVariableError
            If extraneous variables are provided.
        InvalidVariableTypeError
            If any variable value is not a string.
        """
        if not isinstance(variables, Mapping):
            raise TypeError(f"Variables must be a mapping, got {type(variables).__name__}")

        supplied_keys = set(variables.keys())
        declared_keys = set(self._declared_variables)

        # Check for missing keys
        missing_keys = [key for key in self._declared_variables if key not in variables or variables[key] is None]
        if missing_keys:
            raise MissingVariableError(
                f"Missing required template variable: '{missing_keys[0]}'. "
                f"Required: {list(self._declared_variables)}, Provided: {list(variables.keys())}"
            )

        # Check for unknown keys
        unknown_keys = sorted(supplied_keys - declared_keys)
        if unknown_keys:
            raise UnknownVariableError(
                f"Unknown template variable provided: '{unknown_keys[0]}'. "
                f"Declared variables: {list(self._declared_variables)}"
            )

        # Validate types and create sanitized string mapping
        validated: dict[str, str] = {}
        for key in self._declared_variables:
            val = variables[key]
            if not isinstance(val, str):
                raise InvalidVariableTypeError(
                    f"Variable '{key}' must be a string, got {type(val).__name__}."
                )
            validated[key] = val

        return validated

    def render(self, variables: Mapping[str, Any]) -> RenderedPrompt:
        """
        Validate variables and render the final prompt keeping user data distinct
        from fixed instruction fields and preserving literal braces in user data.
        """
        validated_data = self.validate_variables(variables)

        # Check if user data contains literal braces
        has_literal_braces = any("{" in val or "}" in val for val in validated_data.values())

        if self._delimitation_style == DelimitationStyle.RAW:
            data_lines = [f"{k}: {v}" for k, v in validated_data.items()]
            rendered = (
                f"=== INSTRUCTION ===\n"
                f"{self._instruction}\n\n"
                f"=== USER DATA ===\n"
                + "\n".join(data_lines)
            )

        elif self._delimitation_style == DelimitationStyle.TAGGED:
            fields_xml = "\n".join(
                f'  <field name="{k}">{v}</field>' for k, v in validated_data.items()
            )
            rendered = (
                f"<instruction>\n"
                f"{self._instruction}\n"
                f"</instruction>\n"
                f"<user_data>\n"
                f"{fields_xml}\n"
                f"</user_data>"
            )

        elif self._delimitation_style == DelimitationStyle.ENVELOPE:
            envelope_obj = {
                "instruction": self._instruction,
                "user_data": validated_data,
            }
            rendered = json.dumps(envelope_obj, indent=2)

        else:
            raise ValueError(f"Unsupported delimitation style: {self._delimitation_style}")

        return RenderedPrompt(
            instruction=self._instruction,
            declared_variables=self._declared_variables,
            user_data=validated_data,
            rendered_text=rendered,
            delimitation_style=self._delimitation_style.value,
            contains_raw_literal_braces=has_literal_braces,
            semantic_injection_prevented_by_templating_alone=False,
        )


def render_prompt(
    instruction: str,
    variables: Mapping[str, Any],
    declared_variables: Sequence[str] = ("name", "topic"),
    delimitation_style: str | DelimitationStyle = DelimitationStyle.TAGGED,
) -> RenderedPrompt:
    """
    Convenience function to create a PromptTemplate and render it.
    """
    template = PromptTemplate(
        instruction=instruction,
        declared_variables=declared_variables,
        delimitation_style=delimitation_style,
    )
    return template.render(variables)


def compare_configurations(
    instruction: str,
    variables: Mapping[str, Any],
    declared_variables: Sequence[str] = ("name", "topic"),
) -> dict[str, dict[str, Any]]:
    """
    Compare three small controlled configurations (RAW, TAGGED, ENVELOPE)
    using metrics appropriate to this contract:
      - validation_correctness
      - literal_brace_preservation
      - structural_overhead_bytes
      - semantic_injection_prevented_by_templating_alone
    """
    results: dict[str, dict[str, Any]] = {}
    total_raw_input_bytes = sum(len(k) + len(str(v)) for k, v in variables.items())

    for style in [DelimitationStyle.RAW, DelimitationStyle.TAGGED, DelimitationStyle.ENVELOPE]:
        tmpl = PromptTemplate(
            instruction=instruction,
            declared_variables=declared_variables,
            delimitation_style=style,
        )
        rendered = tmpl.render(variables)

        # Check literal preservation: every supplied value must appear byte-for-byte in rendered text
        # (for JSON envelope, check json-decoded user_data value)
        if style == DelimitationStyle.ENVELOPE:
            decoded = json.loads(rendered.rendered_text)
            brace_preserved = all(
                decoded["user_data"][k] == variables[k] for k in variables
            )
        else:
            brace_preserved = all(
                str(v) in rendered.rendered_text for v in variables.values()
            )

        results[style.value] = {
            "validation_correctness": True,
            "brace_preserved": brace_preserved,
            "output_length_chars": len(rendered.rendered_text),
            "structural_overhead_chars": len(rendered.rendered_text) - total_raw_input_bytes,
            "semantic_injection_prevented": rendered.semantic_injection_prevented_by_templating_alone,
        }

    return results


def compare_input_sizes(
    instruction: str,
    fixtures: Mapping[str, Mapping[str, str]],
    delimitation_style: str | DelimitationStyle = DelimitationStyle.TAGGED,
) -> dict[str, dict[str, Any]]:
    """
    Compare three small controlled input sizes (e.g. Small, Medium, Large)
    evaluating correctness, literal preservation, and character expansion.
    """
    results: dict[str, dict[str, Any]] = {}
    tmpl = PromptTemplate(
        instruction=instruction,
        declared_variables=("name", "topic"),
        delimitation_style=delimitation_style,
    )

    for size_label, payload in fixtures.items():
        rendered = tmpl.render(payload)
        raw_size = sum(len(k) + len(v) for k, v in payload.items())
        all_preserved = all(v in rendered.rendered_text for v in payload.values())

        results[size_label] = {
            "input_chars": raw_size,
            "output_chars": len(rendered.rendered_text),
            "expansion_ratio": round(len(rendered.rendered_text) / max(raw_size, 1), 2),
            "braces_preserved": all_preserved,
            "correctness": True,
            "semantic_injection_prevented": rendered.semantic_injection_prevented_by_templating_alone,
        }

    return results
