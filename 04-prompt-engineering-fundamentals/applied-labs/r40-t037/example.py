"""
R40-T037 · Applied Lab: Prompt-Template Escaping & Worked Example with Checks
=============================================================================

This module extends Lesson 04 ("Prompt Engineering Fundamentals") by implementing
a safe prompt template engine that validates declared variables, keeps user data
distinct from fixed instructions, preserves literal braces inside user input, and
publishes an input-to-output worked explanation verified by a regression test.

Lesson connection
-----------------
Lesson 04 introduces prompt components (instructions, context, user input, output
formatting). In production prompt engineering:
  1. Prompts are built dynamically using templates with declared variables.
  2. Input variables must be validated against a declared schema: missing required keys
     (like 'topic') or unrecognized keys must be rejected before sending queries to an LLM.
  3. Literal braces inside user text (e.g., code snippets, math equations `{x | x > 0}`,
     or JSON payloads) must not cause format-string crashes or template escape vulnerabilities.
  4. User data must be isolated from the fixed system instruction fields using explicit
     delimiters to avoid instruction/data confusion.
  5. Templating alone does NOT prevent prompt injection: while strict templating preserves
     structural boundaries, downstream LLMs interpret token semantics. An adversarial
     override ("Ignore previous instructions...") inside user data will still be read
     semantically by the model.

Simplification boundary
-----------------------
This local implementation operates purely as an in-memory string validator and renderer.
It does NOT:
  - Call Azure OpenAI, OpenAI, or third-party cloud LLM endpoints.
  - Download or evaluate neural network weights.
  - Claim real-world model accuracy, prompt robustness, or semantic injection immunity.

Focus: Worked Input-to-Output Explanation & Regression Test
-----------------------------------------------------------
This lab provides `run_worked_example()`: a step-by-step trace showing the transformation
from raw inputs to validated boundary-isolated prompt text. The exact output is pinned
and verified by an automated regression test in `test_example.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class TemplateValidationError(ValueError):
    """Base exception for prompt template validation failures."""
    pass


class MissingVariableError(TemplateValidationError):
    """Raised when a required declared variable is missing from supplied inputs."""
    pass


class UnknownVariableError(TemplateValidationError):
    """Raised when undeclared variables are supplied to the template."""
    pass


class InvalidVariableTypeError(TemplateValidationError, TypeError):
    """Raised when a supplied variable is not a string."""
    pass


@dataclass(frozen=True)
class RenderedPrompt:
    """
    Immutable representation of a rendered, boundary-isolated prompt.

    Attributes
    ----------
    instruction : str
        The fixed system instruction.
    declared_variables : tuple[str, ...]
        Declared variable names for the template.
    user_data : dict[str, str]
        Validated user data mapping.
    rendered_text : str
        Assembled prompt with structural delimiters.
    contains_literal_braces : bool
        Whether any user data value contained literal '{' or '}' characters.
    semantic_injection_prevented_by_templating_alone : bool
        Always False. Templating isolates syntax, not semantic meaning.
    """
    instruction: str
    declared_variables: tuple[str, ...]
    user_data: dict[str, str]
    rendered_text: str
    contains_literal_braces: bool
    semantic_injection_prevented_by_templating_alone: bool = False


@dataclass(frozen=True)
class WorkedExampleStep:
    """An individual phase in the input-to-output pipeline."""
    step_number: int
    title: str
    explanation: str
    state_summary: str


@dataclass(frozen=True)
class WorkedExampleWalkthrough:
    """Complete worked input-to-output explanation with audit trace."""
    input_fixture: dict[str, Any]
    steps: tuple[WorkedExampleStep, ...]
    rendered_prompt: RenderedPrompt
    explanation_markdown: str


class SafePromptTemplate:
    """
    Safe prompt template engine with strict variable validation and boundary isolation.
    """

    def __init__(
        self,
        instruction: str,
        declared_variables: Sequence[str] = ("name", "topic"),
    ) -> None:
        if not instruction or not isinstance(instruction, str):
            raise ValueError("Instruction must be a non-empty string.")

        self._instruction = instruction.strip()
        self._declared_variables = tuple(declared_variables)

    @property
    def instruction(self) -> str:
        return self._instruction

    @property
    def declared_variables(self) -> tuple[str, ...]:
        return self._declared_variables

    def validate_variables(self, variables: Mapping[str, Any]) -> dict[str, str]:
        """
        Validate inputs against declared variables.
        """
        if not isinstance(variables, Mapping):
            raise TypeError(f"Variables must be a mapping, got {type(variables).__name__}")

        supplied_keys = set(variables.keys())
        declared_keys = set(self._declared_variables)

        # Check for missing keys
        missing_keys = [k for k in self._declared_variables if k not in variables or variables[k] is None]
        if missing_keys:
            raise MissingVariableError(
                f"Missing required template variable: '{missing_keys[0]}'. "
                f"Declared variables: {list(self._declared_variables)}"
            )

        # Check for unknown keys
        unknown_keys = sorted(supplied_keys - declared_keys)
        if unknown_keys:
            raise UnknownVariableError(
                f"Unknown template variable provided: '{unknown_keys[0]}'. "
                f"Declared variables: {list(self._declared_variables)}"
            )

        # Validate types
        validated: dict[str, str] = {}
        for key in self._declared_variables:
            val = variables[key]
            if not isinstance(val, str) or isinstance(val, bool):
                raise InvalidVariableTypeError(
                    f"Variable '{key}' must be a string, got {type(val).__name__}."
                )
            validated[key] = val

        return validated

    def render(self, variables: Mapping[str, Any]) -> RenderedPrompt:
        """
        Render prompt keeping fixed instruction distinct from user data,
        preserving literal braces in user data.
        """
        validated_data = self.validate_variables(variables)
        has_literal_braces = any("{" in v or "}" in v for v in validated_data.values())

        # Render with distinct instruction and user data blocks
        data_fields = "\n".join(
            f'  <field name="{k}">{v}</field>' for k, v in validated_data.items()
        )
        rendered_text = (
            f"<instruction>\n"
            f"{self._instruction}\n"
            f"</instruction>\n"
            f"<user_data>\n"
            f"{data_fields}\n"
            f"</user_data>"
        )

        return RenderedPrompt(
            instruction=self._instruction,
            declared_variables=self._declared_variables,
            user_data=validated_data,
            rendered_text=rendered_text,
            contains_literal_braces=has_literal_braces,
            semantic_injection_prevented_by_templating_alone=False,
        )


# ---------------------------------------------------------------------------
# Focus: Worked Input-to-Output Explanation & Regression Fixture
# ---------------------------------------------------------------------------

WORKED_EXAMPLE_INSTRUCTION = "You are an educational tutor. Explain the given topic to the student clearly."

WORKED_EXAMPLE_INPUTS: dict[str, str] = {
    "name": "Alice {Curious Student}",
    "topic": "Photosynthesis {Chlorophyll & Light Reactions: 6CO2 + 6H2O -> C6H12O6 + 6O2}",
}

PINNED_WORKED_EXAMPLE_OUTPUT: str = (
    "<instruction>\n"
    "You are an educational tutor. Explain the given topic to the student clearly.\n"
    "</instruction>\n"
    "<user_data>\n"
    '  <field name="name">Alice {Curious Student}</field>\n'
    '  <field name="topic">Photosynthesis {Chlorophyll & Light Reactions: 6CO2 + 6H2O -> C6H12O6 + 6O2}</field>\n'
    "</user_data>"
)


def run_worked_example() -> WorkedExampleWalkthrough:
    """
    Executes the worked example pipeline and returns a detailed step-by-step
    explanation from raw inputs to the final rendered prompt.
    """
    template = SafePromptTemplate(
        instruction=WORKED_EXAMPLE_INSTRUCTION,
        declared_variables=("name", "topic"),
    )

    steps = (
        WorkedExampleStep(
            step_number=1,
            title="Declared Variable Contract Check",
            explanation=(
                "The template declares exactly ('name', 'topic'). Supplied inputs are inspected: "
                "both keys exist, no keys are missing, and no unexpected keys are present."
            ),
            state_summary="Keys verified: ['name', 'topic'] present and matched.",
        ),
        WorkedExampleStep(
            step_number=2,
            title="Type Validation",
            explanation=(
                "All supplied values are verified to be strings. Non-strings or None values "
                "are rejected to prevent format anomalies."
            ),
            state_summary="Types verified: name is str, topic is str.",
        ),
        WorkedExampleStep(
            step_number=3,
            title="Literal Brace Preservation (Escaping Avoidance)",
            explanation=(
                "User data contains literal curly braces: '{Curious Student}' and formula braces. "
                "Using standard Python str.format() would fail with KeyError or corrupt the braces. "
                "Our single-pass literal substitution inserts values verbatim without re-evaluating braces."
            ),
            state_summary="Literal braces detected and preserved byte-for-byte.",
        ),
        WorkedExampleStep(
            step_number=4,
            title="Instruction/Data Boundary Isolation",
            explanation=(
                "The fixed system instruction is placed inside an <instruction> tag block. "
                "User data is placed in a separate <user_data> block with named fields. "
                "This ensures the model receives a clear demarcation between instructions and untrusted input."
            ),
            state_summary="Delimiters applied: <instruction> and <user_data> blocks generated.",
        ),
        WorkedExampleStep(
            step_number=5,
            title="Prompt Injection Disclaimer",
            explanation=(
                "Notice that templating guarantees syntactic structure, but NOT semantic immunity. "
                "If user data contained 'Ignore instructions', the text is placed inside <user_data>, "
                "but downstream LLMs read all tokens semantically. Real defenses require system prompt "
                "hardening and output filtering."
            ),
            state_summary="semantic_injection_prevented_by_templating_alone is explicitly False.",
        ),
    )

    rendered = template.render(WORKED_EXAMPLE_INPUTS)

    explanation_md = (
        "### Worked Input-to-Output Explanation\n\n"
        f"**1. Input Data:**\n"
        f"- `name`: `{WORKED_EXAMPLE_INPUTS['name']}`\n"
        f"- `topic`: `{WORKED_EXAMPLE_INPUTS['topic']}`\n\n"
        f"**2. Processing Pipeline:**\n"
        f"Each step validates keys, guarantees type safety, preserves curly braces literally, "
        f"and fences user input away from the fixed instruction.\n\n"
        f"**3. Rendered Output:**\n"
        f"```xml\n{rendered.rendered_text}\n```\n"
    )

    return WorkedExampleWalkthrough(
        input_fixture=WORKED_EXAMPLE_INPUTS,
        steps=steps,
        rendered_prompt=rendered,
        explanation_markdown=explanation_md,
    )
