from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from config import LOW_RISK_MAX, MEDIUM_RISK_MAX
from core.risk_evaluator import RiskEvaluator
from tools.tool_stubs import (
    check_device_status,
    check_device_swap,
    check_sim_swap,
    trigger_number_verification,
)


class AgentGuardState(TypedDict, total=False):
    final_decision: str
    final_reasoning: str
    risk_score: int
    risk_level: str
    risk_flags: list[str]
    telecom_signals: dict[str, dict | None]
    request_payload: dict


def evaluate_risk(state: AgentGuardState) -> AgentGuardState:
    assessment = RiskEvaluator().evaluate(state["request_payload"])
    return {
        "risk_score": assessment["risk_score"],
        "risk_level": assessment["risk_level"],
        "risk_flags": assessment["flags"],
        "final_reasoning": assessment["reasoning"],
        "telecom_signals": {
            "sim_swap": None,
            "device_status": None,
            "device_swap": None,
            "number_verification": None,
        },
    }


def check_telecom(state: AgentGuardState) -> AgentGuardState:
    phone_number = state["request_payload"]["phone_number"]
    signals = state["telecom_signals"].copy()
    signals["sim_swap"] = check_sim_swap(phone_number)
    signals["device_status"] = check_device_status(phone_number)
    if state["risk_level"] == "HIGH":
        signals["device_swap"] = check_device_swap(phone_number)
        signals["number_verification"] = trigger_number_verification(phone_number)
    return {"telecom_signals": signals}


def make_decision(state: AgentGuardState) -> AgentGuardState:
    score = state["risk_score"]
    decision = "APPROVED" if score <= LOW_RISK_MAX else "STEP_UP" if score <= MEDIUM_RISK_MAX else "BLOCKED"
    reasoning = state["final_reasoning"]
    signals = state["telecom_signals"]

    flag_triggered = False

    sim_swap = signals.get("sim_swap")
    if sim_swap and sim_swap.get("swapped"):
        flag_triggered = True
        reasoning += " Recent SIM swap detected on approver's number."

    device_swap = signals.get("device_swap")
    if device_swap and device_swap.get("device_swapped"):
        flag_triggered = True
        reasoning += " SIM re-paired with a different physical device."

    device_status = signals.get("device_status")
    if device_status and device_status.get("status") == "NOT_CONNECTED":
        flag_triggered = True
        reasoning += " Approver's device is unreachable."

    if flag_triggered and decision == "APPROVED":
        decision = "STEP_UP"

    number_verification = signals.get("number_verification")
    if number_verification is not None:
        if number_verification.get("verified") is True:
            if decision == "BLOCKED":
                decision = "STEP_UP"
                reasoning += " Number Verification confirmed the approver's identity; escalating for human review instead of auto-blocking."
            elif flag_triggered:
                decision = "STEP_UP"
                reasoning += " Number Verification succeeded, but a telecom risk flag remains."
            else:
                decision = "APPROVED"
                reasoning += " Number Verification confirmed the approver's identity."
        else:
            decision = "BLOCKED"
            reasoning += " Number Verification failed — blocking the action."

    return {"final_decision": decision, "final_reasoning": reasoning}


def _route_after_risk(state: AgentGuardState) -> str:
    return "make_decision" if state["risk_level"] == "LOW" else "check_telecom"


def _build_graph():
    graph = StateGraph(AgentGuardState)
    graph.add_node("evaluate_risk", evaluate_risk)
    graph.add_node("check_telecom", check_telecom)
    graph.add_node("make_decision", make_decision)
    graph.set_entry_point("evaluate_risk")
    graph.add_conditional_edges(
        "evaluate_risk",
        _route_after_risk,
        {"check_telecom": "check_telecom", "make_decision": "make_decision"},
    )
    graph.add_edge("check_telecom", "make_decision")
    graph.add_edge("make_decision", END)
    return graph.compile()


_PIPELINE = _build_graph()


def run_agentguard(request_payload: dict) -> dict:
    """Run the AgentGuard pipeline and return the fixed output contract."""
    result = _PIPELINE.invoke({"request_payload": request_payload})
    return {
        "final_decision": result["final_decision"],
        "final_reasoning": result["final_reasoning"],
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "risk_flags": result["risk_flags"],
        "telecom_signals": result["telecom_signals"],
        "request_payload": result["request_payload"],
    }
