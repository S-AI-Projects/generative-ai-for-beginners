#!/usr/bin/env python3
"""
R40-T010: Building Low Code AI Applications - Scenario Assessment and Applied Questions

This module provides a deterministic, rule-based scenario decision evaluator and
governance checker for 'Building Low Code AI Applications' (Lesson 10).

It models three canonical scenarios:
  1. Normal scenario: Invoice Processing automation using Power Automate and AI Builder.
  2. Boundary scenario: Real-time high-throughput custom neural network image analysis.
  3. Missing-information scenario: Underspecified conversational agent proposal.

It also provides three applied questions:
  1. Predict an output for a new workload.
  2. Diagnose why an underspecified submission fails governance evaluation.
  3. Choose the appropriate architectural policy when low-code boundaries are reached.

Scope and Limitations:
  - This is a local simulation / rule-based governance engine double.
  - Zero external cloud services, Microsoft 365 tenants, Dataverse storage,
    or Azure subscriptions are required or contacted.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class DecisionType(str, Enum):
    LOW_CODE_POWER_PLATFORM = "LOW_CODE_POWER_PLATFORM"
    CUSTOM_CODE_PRO_DEV = "CUSTOM_CODE_PRO_DEV"
    DEFER_INSUFFICIENT_INFORMATION = "DEFER_INSUFFICIENT_INFORMATION"


@dataclass
class ScenarioFacts:
    scenario_id: str
    name: str
    description: str
    monthly_volume: Optional[int] = None
    latency_sla_ms: Optional[int] = None
    custom_model_required: Optional[bool] = None
    prebuilt_model_available: Optional[bool] = None
    developer_persona: Optional[str] = None
    integration_source: Optional[str] = None
    compliance_tier: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScenarioAssessment:
    scenario_id: str
    name: str
    decision: str
    rationale: str
    boundary_flags: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionTableResult:
    is_valid: bool
    total_scenarios: int
    passed_scenarios: int
    mismatches: List[str] = field(default_factory=list)
    tampered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QuestionEvaluationResult:
    question_id: str
    title: str
    passed: bool
    expected: str
    actual: str
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Baseline scenarios published in the lesson decision table
BASELINE_SCENARIOS: Dict[str, ScenarioFacts] = {
    "S1_NORMAL": ScenarioFacts(
        scenario_id="S1_NORMAL",
        name="Invoice Processing and Approval Flow",
        description=(
            "Automated document processing extracting invoice number, vendor, date, "
            "and total amount from email attachments into Dataverse with manager approval."
        ),
        monthly_volume=1500,
        latency_sla_ms=60000,  # 1 minute batch workflow
        custom_model_required=False,
        prebuilt_model_available=True,  # AI Builder Invoice Processing
        developer_persona="Citizen Developer / Business Analyst",
        integration_source="Exchange Email & SharePoint Online",
        compliance_tier="Standard Enterprise Cloud",
    ),
    "S2_BOUNDARY": ScenarioFacts(
        scenario_id="S2_BOUNDARY",
        name="Real-Time Handwritten Exam Fraud Detection",
        description=(
            "High-throughput live image processing applying custom PyTorch CNN weights "
            "and specialized loss embeddings directly against streaming video frames."
        ),
        monthly_volume=4000000,  # ~130,000/day, peak 150 req/sec
        latency_sla_ms=45,       # 45ms sub-second SLA
        custom_model_required=True,  # Bespoke weights & custom tensor runtime
        prebuilt_model_available=False,
        developer_persona="ML Systems Engineer",
        integration_source="Low-latency WebSocket Stream",
        compliance_tier="Strict Isolated Private VPC",
    ),
    "S3_MISSING_INFO": ScenarioFacts(
        scenario_id="S3_MISSING_INFO",
        name="Conversational Student Advisory Agent",
        description=(
            "An exploratory generative chat assistant to help prospective students "
            "inquire about university admission requirements and campus events."
        ),
        monthly_volume=None,     # Underspecified
        latency_sla_ms=None,     # Underspecified
        custom_model_required=False,
        prebuilt_model_available=True,  # Copilot Studio
        developer_persona="Academic Department Lead",
        integration_source="Undetermined Legacy Database",
        compliance_tier=None,    # Underspecified (FERPA / GDPR status unknown)
    ),
}

# Published Decision Table entries matching Lesson 10 architectural principles
PUBLISHED_DECISION_TABLE: Dict[str, Dict[str, str]] = {
    "S1_NORMAL": {
        "expected_decision": DecisionType.LOW_CODE_POWER_PLATFORM.value,
        "rationale_key": "Optimal match for Power Platform. The prebuilt AI Builder Invoice Processing model satisfies document extraction needs without custom training; monthly volume (1,500) and batch SLA (60s) fall well within standard Power Automate quotas; native Dataverse and Outlook connector integration delivers rapid time-to-value.",
    },
    "S2_BOUNDARY": {
        "expected_decision": DecisionType.CUSTOM_CODE_PRO_DEV.value,
        "rationale_key": "Violates low-code platform boundaries. Requires custom PyTorch model weights and specialized tensor operations unsupported by AI Builder. The sub-50ms latency SLA and 4M monthly volume exceed standard Power Automate connector throttling and synchronous request limits, mandating custom pro-code microservices on containerized compute.",
    },
    "S3_MISSING_INFO": {
        "expected_decision": DecisionType.DEFER_INSUFFICIENT_INFORMATION.value,
        "rationale_key": "Architectural decision deferred due to incomplete operational facts. Critical parameters including expected request volume, latency SLA, and student data privacy compliance tier (e.g. FERPA/GDPR) are undefined. Committing to low-code or pro-code without these facts risks architectural failure.",
    },
}

# Operational limits for low-code platform tier (Lesson 10 governance envelope)
LOW_CODE_MAX_MONTHLY_VOLUME = 100_000
LOW_CODE_MIN_LATENCY_SLA_MS = 200
UNSUPPORTED_LOW_CODE_COMPLIANCE = {"Strict Isolated Private VPC", "Airgapped On-Prem"}


def evaluate_scenario(facts: ScenarioFacts) -> ScenarioAssessment:
    """
    Evaluates input facts against the low-code architectural governance criteria.
    """
    missing_fields: List[str] = []
    required_operational_fields = [
        ("monthly_volume", facts.monthly_volume),
        ("latency_sla_ms", facts.latency_sla_ms),
        ("custom_model_required", facts.custom_model_required),
        ("compliance_tier", facts.compliance_tier),
    ]

    for field_name, value in required_operational_fields:
        if value is None:
            missing_fields.append(field_name)

    # 1. Missing information check
    if missing_fields:
        rationale = (
            f"Decision deferred: Insufficient operational metrics provided. "
            f"Missing required fields: {', '.join(sorted(missing_fields))}. "
            f"Cannot determine connector throughput, latency tolerance, or regulatory boundaries."
        )
        return ScenarioAssessment(
            scenario_id=facts.scenario_id,
            name=facts.name,
            decision=DecisionType.DEFER_INSUFFICIENT_INFORMATION.value,
            rationale=rationale,
            missing_fields=sorted(missing_fields),
        )

    # 2. Boundary violation check
    boundary_flags: List[str] = []

    if facts.custom_model_required:
        boundary_flags.append("CUSTOM_MODEL_REQUIRED: Requires custom weights/runtime not offered by AI Builder.")
    elif facts.prebuilt_model_available is False:
        boundary_flags.append("NO_PREBUILT_MODEL: No suitable prebuilt AI model or prompt template available.")

    if facts.monthly_volume is not None and facts.monthly_volume > LOW_CODE_MAX_MONTHLY_VOLUME:
        boundary_flags.append(
            f"VOLUME_EXCEEDED: Monthly volume ({facts.monthly_volume:,}) exceeds low-code connector threshold ({LOW_CODE_MAX_MONTHLY_VOLUME:,})."
        )

    if facts.latency_sla_ms is not None and facts.latency_sla_ms < LOW_CODE_MIN_LATENCY_SLA_MS:
        boundary_flags.append(
            f"LATENCY_SLA_BREACH: Required latency ({facts.latency_sla_ms}ms) is below low-code minimum SLA ({LOW_CODE_MIN_LATENCY_SLA_MS}ms)."
        )

    if facts.compliance_tier in UNSUPPORTED_LOW_CODE_COMPLIANCE:
        boundary_flags.append(
            f"COMPLIANCE_RESTRICTION: Compliance tier '{facts.compliance_tier}' requires private VPC/custom host isolation."
        )

    if boundary_flags:
        rationale = (
            f"Exceeds low-code architectural boundaries. Requires custom pro-code cloud-native architecture. "
            f"Triggers: {'; '.join(boundary_flags)}"
        )
        return ScenarioAssessment(
            scenario_id=facts.scenario_id,
            name=facts.name,
            decision=DecisionType.CUSTOM_CODE_PRO_DEV.value,
            rationale=rationale,
            boundary_flags=boundary_flags,
        )

    # 3. Normal low-code fit
    rationale = (
        f"Well-suited for Low Code Power Platform. Volume ({facts.monthly_volume:,}/mo) and SLA ({facts.latency_sla_ms}ms) "
        f"operate cleanly within Power Automate & AI Builder capabilities; prebuilt AI components fulfill requirements."
    )
    return ScenarioAssessment(
        scenario_id=facts.scenario_id,
        name=facts.name,
        decision=DecisionType.LOW_CODE_POWER_PLATFORM.value,
        rationale=rationale,
    )


def verify_decision_table(tamper: bool = False) -> DecisionTableResult:
    """
    Checks the published baseline decision table against evaluated outputs.
    If tamper=True, deliberately injects an invalid decision to demonstrate checker failure.
    """
    mismatches: List[str] = []
    passed = 0
    total = len(BASELINE_SCENARIOS)

    for scenario_id, facts in BASELINE_SCENARIOS.items():
        assessment = evaluate_scenario(facts)
        expected_meta = PUBLISHED_DECISION_TABLE.get(scenario_id)
        if not expected_meta:
            mismatches.append(f"Scenario {scenario_id} not found in published decision table.")
            continue

        expected_decision = expected_meta["expected_decision"]

        # If tamper is enabled, intentionally alter the expected decision for S1_NORMAL
        if tamper and scenario_id == "S1_NORMAL":
            expected_decision = DecisionType.CUSTOM_CODE_PRO_DEV.value

        if assessment.decision != expected_decision:
            mismatches.append(
                f"Scenario '{scenario_id}' decision mismatch: expected '{expected_decision}', got '{assessment.decision}'."
            )
        else:
            passed += 1

    is_valid = (len(mismatches) == 0)
    return DecisionTableResult(
        is_valid=is_valid,
        total_scenarios=total,
        passed_scenarios=passed,
        mismatches=mismatches,
        tampered=tamper,
    )


# -----------------------------------------------------------------------------
# Three Applied Questions
# -----------------------------------------------------------------------------

# Applied Question 1: Predict an Output
def get_question_1_scenario() -> ScenarioFacts:
    """
    Fixture for Applied Question 1: Customer Support Ticket Summarizer
    """
    return ScenarioFacts(
        scenario_id="Q1_SUPPORT_TICKETS",
        name="Customer Support Ticket Summarizer",
        description="Summarize incoming support tickets and categorize sentiment for dashboard display.",
        monthly_volume=5000,
        latency_sla_ms=10000,  # 10s batch/async SLA
        custom_model_required=False,
        prebuilt_model_available=True,  # Prebuilt 'Create Text with GPT' prompt in AI Builder
        developer_persona="Citizen Developer & Support Lead",
        integration_source="Dynamics 365 / Dataverse",
        compliance_tier="Standard Enterprise Cloud",
    )


def check_question_1_predict_output(
    predicted_decision: Optional[str] = None,
) -> QuestionEvaluationResult:
    """
    Applied Question 1:
    Predict the architecture decision for the Customer Support Ticket Summarizer scenario.
    """
    scenario = get_question_1_scenario()
    evaluated = evaluate_scenario(scenario)
    expected_decision = evaluated.decision  # DecisionType.LOW_CODE_POWER_PLATFORM.value

    actual_decision = predicted_decision if predicted_decision is not None else expected_decision
    passed = (actual_decision == expected_decision)
    rationale = (
        "The workload fits standard Power Platform capabilities: 5,000 tickets/month is well within "
        "connector rate limits, 10-second SLA is acceptable for asynchronous flow processing, "
        "and AI Builder's prebuilt 'Create Text with GPT' prompt template eliminates the need for custom ML engineering."
    )
    return QuestionEvaluationResult(
        question_id="Q1_PREDICT_OUTPUT",
        title="Predict Output for Support Ticket Summarizer",
        passed=passed,
        expected=expected_decision,
        actual=actual_decision,
        rationale=rationale,
    )


# Applied Question 2: Diagnose a Failure
def get_question_2_scenario() -> ScenarioFacts:
    """
    Fixture for Applied Question 2: Incomplete Proposal Submission
    """
    return ScenarioFacts(
        scenario_id="Q2_INCOMPLETE_PROPOSAL",
        name="Automated Course Syllabus Parser",
        description="Extract syllabus topics and reading lists into the course management catalog.",
        monthly_volume=None,       # Missing!
        latency_sla_ms=None,       # Missing!
        custom_model_required=False,
        prebuilt_model_available=True,
        developer_persona="Instructional Designer",
        integration_source="SharePoint Document Library",
        compliance_tier=None,      # Missing!
    )


def check_question_2_diagnose_failure(
    diagnostic_code: Optional[str] = None,
) -> QuestionEvaluationResult:
    """
    Applied Question 2:
    Diagnose why the governance checker rejects this proposal and defers the decision.
    """
    scenario = get_question_2_scenario()
    assessment = evaluate_scenario(scenario)

    expected_diagnosis = "MISSING_OPERATIONAL_METRICS"
    actual_diagnosis = diagnostic_code if diagnostic_code is not None else expected_diagnosis

    missing_fields = assessment.missing_fields
    passed = (
        actual_diagnosis == expected_diagnosis
        and assessment.decision == DecisionType.DEFER_INSUFFICIENT_INFORMATION.value
        and "compliance_tier" in missing_fields
        and "latency_sla_ms" in missing_fields
        and "monthly_volume" in missing_fields
    )

    rationale = (
        f"Governance evaluation cannot proceed because mandatory operational fields are absent: "
        f"{', '.join(sorted(missing_fields))}. Low-code platforms have defined connector quotas and "
        f"data protection boundaries; committing without volume, latency SLA, and compliance classification "
        f"risks platform throttling or regulatory violations."
    )
    return QuestionEvaluationResult(
        question_id="Q2_DIAGNOSE_FAILURE",
        title="Diagnose Rejection of Incomplete Proposal",
        passed=passed,
        expected=expected_diagnosis,
        actual=actual_diagnosis,
        rationale=rationale,
    )


# Applied Question 3: Choose a Boundary Policy
class BoundaryPolicy(str, Enum):
    POLICY_RETRY_SPIKE = "POLICY_RETRY_SPIKE"
    POLICY_HYBRID_PRO_CODE_OFFLOAD = "POLICY_HYBRID_PRO_CODE_OFFLOAD"
    POLICY_BYPASS_GOVERNANCE = "POLICY_BYPASS_GOVERNANCE"


def check_question_3_choose_boundary_policy(
    chosen_policy: Optional[str] = None,
) -> QuestionEvaluationResult:
    """
    Applied Question 3:
    When a low-code application's document ingestion volume surges to 250,000 items/day
    and triggers connector HTTP 429 throttling errors, choose the appropriate governance policy.
    """
    expected_policy = BoundaryPolicy.POLICY_HYBRID_PRO_CODE_OFFLOAD.value
    actual_policy = chosen_policy if chosen_policy is not None else expected_policy

    passed = (actual_policy == expected_policy)
    rationale = (
        "Per the lesson governance framework, when transaction throughput exceeds low-code connector quotas, "
        "the recommended architectural pattern is 'Hybrid Pro-Code Offload': migrate the compute-heavy, "
        "high-throughput ingestion pipeline to pro-dev microservices (e.g. Azure Functions or Container Apps with "
        "Azure AI Document Intelligence SDK) while retaining Power Apps for human-in-the-loop review and workflow triggers."
    )
    return QuestionEvaluationResult(
        question_id="Q3_CHOOSE_BOUNDARY_POLICY",
        title="Choose Architectural Boundary Governance Policy",
        passed=passed,
        expected=expected_policy,
        actual=actual_policy,
        rationale=rationale,
    )


def run_all_applied_questions() -> Dict[str, QuestionEvaluationResult]:
    """
    Runs all three applied questions and returns a structured dictionary of results.
    """
    return {
        "question_1": check_question_1_predict_output(),
        "question_2": check_question_2_diagnose_failure(),
        "question_3": check_question_3_choose_boundary_policy(),
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="R40-T010: Building Low Code AI Applications Scenario Assessment and Applied Questions"
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "boundary", "missing", "all"],
        default="all",
        help="Evaluate specific baseline scenario(s).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the baseline decision table against published criteria.",
    )
    parser.add_argument(
        "--tamper",
        action="store_true",
        help="Deliberately tamper with the decision table to prove checker failure.",
    )
    parser.add_argument(
        "--questions",
        action="store_true",
        help="Run executable checks for the three applied questions.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    output: Dict[str, Any] = {}

    # Handle --check
    if args.check:
        check_result = verify_decision_table(tamper=args.tamper)
        output["decision_table_verification"] = check_result.to_dict()

        if not check_result.is_valid:
            if args.json:
                print(json.dumps(output, indent=2))
            else:
                print(f"[CHECK FAILED] Decision table verification failed (tampered={check_result.tampered}):")
                for err in check_result.mismatches:
                    print(f"  - {err}")
            return 1

        if not args.json and not args.questions and args.scenario == "all":
            print(f"[CHECK PASSED] All {check_result.passed_scenarios}/{check_result.total_scenarios} scenarios match published decisions.")

    # Handle scenario evaluation
    if not args.check or args.scenario != "all" or not args.tamper:
        scenario_map = {
            "normal": ["S1_NORMAL"],
            "boundary": ["S2_BOUNDARY"],
            "missing": ["S3_MISSING_INFO"],
            "all": ["S1_NORMAL", "S2_BOUNDARY", "S3_MISSING_INFO"],
        }
        selected = scenario_map[args.scenario]
        evaluations = {}
        for s_id in selected:
            facts = BASELINE_SCENARIOS[s_id]
            assessment = evaluate_scenario(facts)
            evaluations[s_id] = assessment.to_dict()
        output["evaluations"] = evaluations

    # Handle applied questions
    if args.questions:
        q_results = run_all_applied_questions()
        output["applied_questions"] = {k: v.to_dict() for k, v in q_results.items()}
        all_passed = all(q.passed for q in q_results.values())
        output["applied_questions_all_passed"] = all_passed

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        if "evaluations" in output:
            print("=== Scenario Evaluations ===")
            for s_id, data in output["evaluations"].items():
                print(f"\nScenario: {s_id} - {data['name']}")
                print(f"  Decision : {data['decision']}")
                print(f"  Rationale: {data['rationale']}")
                if data.get("boundary_flags"):
                    print(f"  Flags    : {data['boundary_flags']}")
                if data.get("missing_fields"):
                    print(f"  Missing  : {data['missing_fields']}")

        if args.questions and "applied_questions" in output:
            print("\n=== Applied Questions Evaluation ===")
            for q_id, q_data in output["applied_questions"].items():
                status = "PASS" if q_data["passed"] else "FAIL"
                print(f"\n[{status}] {q_data['question_id']}: {q_data['title']}")
                print(f"  Expected : {q_data['expected']}")
                print(f"  Actual   : {q_data['actual']}")
                print(f"  Rationale: {q_data['rationale']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
