"""
Building Low-Code AI Applications: Step Pipeline, State Trace & Invariants (R40-T034).

Demonstrates a low-code automated workflow pipeline (inspired by Power Automate / AI Builder)
with step-by-step intermediate state tracing and formal invariant verification.
"""

from typing import Dict, Any, List, Tuple


DECISION_TABLE: List[Dict[str, Any]] = [
    {
        "id": "scenario_normal",
        "description": "Normal scenario: Critical payment gateway outage requiring emergency routing",
        "input": {
            "submission_id": "SUB-101",
            "text": "Urgent system outage in payment gateway affecting customer checkout.",
            "urgency_flag": True,
            "department": "IT Support",
        },
        "expected_decision": "ROUTE_HIGH_PRIORITY_INCIDENT",
        "expected_routing": "emergency_oncall",
        "rationale": "High-severity keywords identified and urgency flag is set; flow routes immediately to emergency on-call queue.",
    },
    {
        "id": "scenario_boundary",
        "description": "Boundary scenario: Monitored service mentioned with low urgency at priority boundary",
        "input": {
            "submission_id": "SUB-102",
            "text": "Payment gateway response seems slightly sluggish today.",
            "urgency_flag": False,
            "department": "Billing",
        },
        "expected_decision": "ROUTE_STANDARD_TRIAGE",
        "expected_routing": "standard_support",
        "rationale": "Mentions monitored service but severity is below critical threshold and urgency flag is False; routes to standard triage queue.",
    },
    {
        "id": "scenario_missing_info",
        "description": "Missing-information scenario: Unspecified department and brief ambiguous text",
        "input": {
            "submission_id": "SUB-103",
            "text": "Need assistance.",
            "urgency_flag": False,
            "department": "",
        },
        "expected_decision": "REQUEST_MISSING_DETAILS",
        "expected_routing": "clarification_prompt",
        "rationale": "Missing department information and insufficient text detail; triggers clarification step rather than unguided routing.",
    },
]


class LowCodeWorkflowEngine:
    """Simulates a low-code flow engine with observable intermediate state transitions."""

    def __init__(self):
        self.step_history: List[Dict[str, Any]] = []

    def execute_pipeline(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a 3-step low-code flow and records each intermediate state."""
        self.step_history.clear()

        # Step 1: Input Ingestion & Normalization
        text = str(payload.get("text", "")).strip()
        department = str(payload.get("department", "")).strip()
        urgency = bool(payload.get("urgency_flag", False))
        submission_id = str(payload.get("submission_id", "UNKNOWN"))

        step_1_state = {
            "step_name": "INGESTION",
            "submission_id": submission_id,
            "char_count": len(text),
            "department": department,
            "urgency_flag": urgency,
        }
        self.step_history.append(step_1_state)

        # Step 2: AI Enrichment (classification simulation)
        is_missing_info = (not department) or (len(text) < 20)
        has_critical_kw = any(w in text.lower() for w in ["outage", "critical", "emergency", "fatal"])

        if has_critical_kw:
            severity_score = 0.95
        elif "sluggish" in text.lower() or "slow" in text.lower() or "delay" in text.lower():
            severity_score = 0.50
        else:
            severity_score = 0.20

        step_2_state = {
            "step_name": "AI_ENRICHMENT",
            "has_critical_keywords": has_critical_kw,
            "severity_score": severity_score,
            "is_missing_info": is_missing_info,
        }
        self.step_history.append(step_2_state)

        # Step 3: Decision Gate & Routing
        if is_missing_info:
            decision = "REQUEST_MISSING_DETAILS"
            routing = "clarification_prompt"
        elif severity_score >= 0.8 or (severity_score >= 0.5 and urgency):
            decision = "ROUTE_HIGH_PRIORITY_INCIDENT"
            routing = "emergency_oncall"
        else:
            decision = "ROUTE_STANDARD_TRIAGE"
            routing = "standard_support"

        step_3_state = {
            "step_name": "DECISION_GATE",
            "decision": decision,
            "routing": routing,
        }
        self.step_history.append(step_3_state)

        final_output = {
            "submission_id": submission_id,
            "decision": decision,
            "routing": routing,
            "step_count": len(self.step_history),
            "intermediate_states": list(self.step_history),
        }
        return final_output


def verify_pipeline_invariant(intermediate_states: List[Dict[str, Any]], final_output: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Tests the invariant linking intermediate states to the final output:
    1. Exactly 3 ordered steps must be recorded: INGESTION, AI_ENRICHMENT, DECISION_GATE.
    2. Final output decision and routing must strictly match Step 3 DECISION_GATE state.
    3. If Step 2 flagged is_missing_info, final decision must be REQUEST_MISSING_DETAILS.
    4. If Step 2 flagged critical severity, final decision must be ROUTE_HIGH_PRIORITY_INCIDENT.
    """
    violations = []

    if len(intermediate_states) != 3:
        violations.append(f"Invariant broken: Expected 3 steps, found {len(intermediate_states)}")
        return False, violations

    step_names = [s["step_name"] for s in intermediate_states]
    if step_names != ["INGESTION", "AI_ENRICHMENT", "DECISION_GATE"]:
        violations.append(f"Invariant broken: Invalid step sequence {step_names}")

    gate_state = intermediate_states[2]
    if final_output["decision"] != gate_state["decision"]:
        violations.append("Invariant broken: Final decision does not match step 3 gate decision")
    if final_output["routing"] != gate_state["routing"]:
        violations.append("Invariant broken: Final routing does not match step 3 gate routing")

    enrich_state = intermediate_states[1]
    if enrich_state["is_missing_info"] and final_output["decision"] != "REQUEST_MISSING_DETAILS":
        violations.append("Invariant broken: Missing info was flagged but decision is not REQUEST_MISSING_DETAILS")

    if enrich_state["has_critical_keywords"] and final_output["decision"] != "ROUTE_HIGH_PRIORITY_INCIDENT":
        violations.append("Invariant broken: Critical keywords flagged but decision is not ROUTE_HIGH_PRIORITY_INCIDENT")

    return (len(violations) == 0, violations)


def check_decision_table(table: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Checks the published decision table and validates invariants across all scenarios."""
    errors = []
    engine = LowCodeWorkflowEngine()

    for item in table:
        output = engine.execute_pipeline(item["input"])
        if output["decision"] != item["expected_decision"]:
            errors.append(f"{item['id']}: expected '{item['expected_decision']}', got '{output['decision']}'")
        if output["routing"] != item["expected_routing"]:
            errors.append(f"{item['id']}: expected routing '{item['expected_routing']}', got '{output['routing']}'")

        valid_invariant, violations = verify_pipeline_invariant(output["intermediate_states"], output)
        if not valid_invariant:
            errors.extend([f"{item['id']}: {v}" for v in violations])

    return (len(errors) == 0, errors)
