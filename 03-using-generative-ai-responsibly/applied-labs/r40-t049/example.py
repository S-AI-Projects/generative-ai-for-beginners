"""
R40-T049 · Applied Lab: Responsible Action Policy & Pre-Execution Validation
============================================================================

This module illustrates Lesson 03 ("Using Generative AI Responsibly") by
implementing an **action policy validator** that intercepts proposed LLM
agent actions before execution.

Lesson connection
-----------------
Lesson 03 establishes that responsible generative AI systems must enforce
Safety System guardrails (Reliability/Safety, Accountability) between the
generative model output and downstream side-effects.

When an LLM produces an action or tool call:
  1. The action must be evaluated against an **explicit allowed-tool set**.
  2. If allowed, arguments must be validated against a **per-tool argument schema**.
  3. If rejected (e.g. unknown tool or missing required argument), a refusal trace
     is emitted, and the action **never reaches the stub executor**.
  4. Only validated actions proceed to execution.

Controlled Configurations
-------------------------
We compare three controlled policy configurations across an identical action test suite:
  - Configuration A (Strict Read-Only): allows only ``read``
  - Configuration B (Standard Inspection): allows ``read`` and ``search``
  - Configuration C (Extended Assistant): allows ``read``, ``search``, and ``summarize``

Metric:
  - Interception Rate (% of actions blocked)
  - Execution Pass-Through Count
  - Executor Zero-Leakage Invariant (0 rejected actions reach executor)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


REASON_UNKNOWN_TOOL = "UNKNOWN_TOOL"
REASON_MISSING_ARGUMENT = "MISSING_REQUIRED_ARGUMENT"
REASON_INVALID_ARGUMENT_TYPE = "INVALID_ARGUMENT_TYPE"
REASON_EMPTY_ARGUMENT = "EMPTY_ARGUMENT"


@dataclass(frozen=True)
class ToolSchema:
    """Argument specification for a single permitted tool."""
    name: str
    required_args: tuple[str, ...] = ()
    arg_types: dict[str, type] = field(default_factory=dict)


@dataclass(frozen=True)
class Action:
    """A proposed tool action with parameters."""
    tool: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RefusalTrace:
    """Detailed record of why an action was blocked from execution."""
    reason: str
    tool: str
    message: str
    offending_arg: str | None = None


@dataclass(frozen=True)
class ActionResult:
    """The result of evaluating and optionally executing a proposed action."""
    action: Action
    executed: bool
    refusal: RefusalTrace | None = None
    output: Any = None


class StubExecutor:
    """
    Local mock executor that simulates side-effects.

    Records every action that reaches it. Used to verify the crucial safety
    invariant: rejected actions NEVER reach the executor.
    """

    def __init__(self) -> None:
        self.executed_actions: list[Action] = []

    def execute(self, action: Action) -> str:
        """Record execution and return a simulated response string."""
        self.executed_actions.append(action)
        if action.tool == "read":
            return f"Mock content from {action.args.get('path')}"
        if action.tool == "search":
            return f"Mock search results for {action.args.get('query')}"
        if action.tool == "summarize":
            return f"Mock summary of {action.args.get('text')}"
        return f"Mock execution of {action.tool}"


class ActionPolicyValidator:
    """
    Evaluates proposed actions against allowed-tool set and argument schema.
    """

    def __init__(self, allowed_tools: Mapping[str, ToolSchema]) -> None:
        self.allowed_tools: dict[str, ToolSchema] = dict(allowed_tools)

    def validate_action(self, action: Action) -> RefusalTrace | None:
        """
        Validate action against policy and schema without executing.

        Returns None if valid, or a RefusalTrace if rejected.
        """
        # Step 1: Tool membership check
        if action.tool not in self.allowed_tools:
            return RefusalTrace(
                reason=REASON_UNKNOWN_TOOL,
                tool=action.tool,
                message=f"Tool '{action.tool}' is not in the allowed tool set.",
            )

        schema = self.allowed_tools[action.tool]

        # Step 2: Required argument check
        for req in schema.required_args:
            if req not in action.args:
                return RefusalTrace(
                    reason=REASON_MISSING_ARGUMENT,
                    tool=action.tool,
                    offending_arg=req,
                    message=f"Missing required argument '{req}' for tool '{action.tool}'.",
                )
            val = action.args[req]
            if val is None or (isinstance(val, str) and not val.strip()):
                return RefusalTrace(
                    reason=REASON_EMPTY_ARGUMENT,
                    tool=action.tool,
                    offending_arg=req,
                    message=f"Required argument '{req}' cannot be empty.",
                )

        # Step 3: Type check
        for arg_name, expected_type in schema.arg_types.items():
            if arg_name in action.args:
                val = action.args[arg_name]
                if not isinstance(val, expected_type):
                    return RefusalTrace(
                        reason=REASON_INVALID_ARGUMENT_TYPE,
                        tool=action.tool,
                        offending_arg=arg_name,
                        message=f"Argument '{arg_name}' must be of type {expected_type.__name__}.",
                    )

        return None

    def evaluate_and_execute(self, action: Action, executor: StubExecutor) -> ActionResult:
        """
        Validate proposed action; only forward to executor if validation passes.
        """
        refusal = self.validate_action(action)
        if refusal is not None:
            # SAFETY INVARIANT: rejected actions NEVER reach the executor
            return ActionResult(action=action, executed=False, refusal=refusal, output=None)

        output = executor.execute(action)
        return ActionResult(action=action, executed=True, refusal=None, output=output)


# ---------------------------------------------------------------------------
# Pre-defined Controlled Configurations
# ---------------------------------------------------------------------------

CONFIG_STRICT_READ = {
    "read": ToolSchema(name="read", required_args=("path",), arg_types={"path": str}),
}

CONFIG_STANDARD_INSPECTION = {
    "read": ToolSchema(name="read", required_args=("path",), arg_types={"path": str}),
    "search": ToolSchema(name="search", required_args=("query",), arg_types={"query": str}),
}

CONFIG_EXTENDED_ASSISTANT = {
    "read": ToolSchema(name="read", required_args=("path",), arg_types={"path": str}),
    "search": ToolSchema(name="search", required_args=("query",), arg_types={"query": str}),
    "summarize": ToolSchema(name="summarize", required_args=("text",), arg_types={"text": str}),
}


@dataclass(frozen=True)
class PolicyComparisonMetric:
    config_name: str
    total_actions: int
    executed_count: int
    rejected_count: int
    interception_rate: float
    executor_leakage_count: int  # Must be 0


def compare_policy_configurations(
    actions: Sequence[Action],
) -> dict[str, PolicyComparisonMetric]:
    """
    Compare three small controlled configurations across an identical action workload.
    """
    configs = {
        "Config_A_StrictRead": CONFIG_STRICT_READ,
        "Config_B_StandardInspection": CONFIG_STANDARD_INSPECTION,
        "Config_C_ExtendedAssistant": CONFIG_EXTENDED_ASSISTANT,
    }

    metrics: dict[str, PolicyComparisonMetric] = {}

    for name, schema_map in configs.items():
        validator = ActionPolicyValidator(schema_map)
        executor = StubExecutor()

        executed = 0
        rejected = 0
        leakage = 0

        for action in actions:
            res = validator.evaluate_and_execute(action, executor)
            if res.executed:
                executed += 1
            else:
                rejected += 1
                # Check for leakage: did this action somehow end up in executor?
                if action in executor.executed_actions:
                    leakage += 1

        total = len(actions)
        interception_rate = (rejected / total) if total > 0 else 0.0

        metrics[name] = PolicyComparisonMetric(
            config_name=name,
            total_actions=total,
            executed_count=executed,
            rejected_count=rejected,
            interception_rate=interception_rate,
            executor_leakage_count=leakage,
        )

    return metrics
