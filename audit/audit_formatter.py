"""
audit/audit_formatter.py
-------------------------
Turns the raw pipeline output into human-readable summary strings
and a clean, structured audit entry ready to write to Supabase.

Phase 2 of the project spec.
"""

from datetime import datetime, timezone

RAW_REQUEST_SNIPPET_MAX_LEN = 200

DECISION_DISPLAY_MAP = {
    "APPROVED": "✅ APPROVED",
    "STEP_UP": "⚠️ STEP-UP VERIFICATION REQUIRED",
    "BLOCKED": "❌ BLOCKED",
}

FLAG_DISPLAY_MAP = {
    "URGENCY_LANGUAGE": "Urgency/pressure language detected in request",
    "NEW_VENDOR": "New or unknown vendor relationship",
    "BANK_DETAIL_CHANGE": "Bank detail change request",
    "FIRST_TIME_CHANGE": "First-time bank detail change for this vendor",
    "OVERRIDE_INSTRUCTION": "Request contains override/bypass instructions",
    "EVALUATION_ERROR": "Risk evaluation encountered an error — defaulted to HIGH",
}


def get_decision_display(decision):
    """Maps a decision string to its display string. Unknown -> BLOCKED display."""
    return DECISION_DISPLAY_MAP.get(decision, DECISION_DISPLAY_MAP["BLOCKED"])


def format_telecom_summary(telecom_signals):
    """
    Converts the raw telecom_signals dict into a single readable summary
    string, following the Telecom Summary Format spec. Never raises —
    missing/malformed input just yields fewer parts (or the "no checks"
    message).
    """
    if not isinstance(telecom_signals, dict):
        telecom_signals = {}

    parts = []

    sim_swap = telecom_signals.get("sim_swap")
    if isinstance(sim_swap, dict):
        if sim_swap.get("swapped"):
            days_since_swap = sim_swap.get("days_since_swap", "unknown")
            parts.append(f"⚠️ SIM swap detected {days_since_swap} day(s) ago")
        else:
            parts.append("✅ SIM swap: clean")

    device_status = telecom_signals.get("device_status")
    if isinstance(device_status, dict):
        if device_status.get("reachable"):
            parts.append("✅ Device status: reachable and normal")
        else:
            parts.append("⚠️ Device status: UNREACHABLE")

    device_swap = telecom_signals.get("device_swap")
    if isinstance(device_swap, dict):
        if device_swap.get("device_swapped"):
            parts.append("⚠️ Device swap detected")
        else:
            parts.append("✅ Device swap: clean")

    number_verification = telecom_signals.get("number_verification")
    if isinstance(number_verification, dict):
        if number_verification.get("verified"):
            parts.append("✅ Number verification: human confirmed on device")
        else:
            parts.append("❌ Number verification: FAILED")

    if not parts:
        return "No telecom checks performed"

    return " | ".join(parts)


def format_flags_summary(risk_flags):
    """
    Converts the raw risk_flags list into a single readable summary
    string, following the Flags Summary Format spec. Unknown flags are
    shown as-is. Never raises.
    """
    if not risk_flags or not isinstance(risk_flags, (list, tuple)):
        return "No red flags detected"

    described = [FLAG_DISPLAY_MAP.get(flag, str(flag)) for flag in risk_flags]

    if not described:
        return "No red flags detected"

    return " | ".join(described)


def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def build_audit_entry(pipeline_output):
    """
    Main formatter entry point (Phase 2, step 4).

    Takes the full pipeline output dict (already sanitized with safe
    defaults by the Decision Engine) and returns a clean, structured
    audit entry dict with every field the `audit_logs` table expects.

    Never raises: every field is pulled defensively with a safe default.
    """
    pipeline_output = pipeline_output if isinstance(pipeline_output, dict) else {}

    decision = pipeline_output.get("final_decision") or "BLOCKED"
    if decision not in DECISION_DISPLAY_MAP:
        decision = "BLOCKED"

    risk_flags = pipeline_output.get("risk_flags") or []
    if not isinstance(risk_flags, list):
        risk_flags = []

    telecom_signals = pipeline_output.get("telecom_signals") or {}
    if not isinstance(telecom_signals, dict):
        telecom_signals = {}

    request_payload = pipeline_output.get("request_payload") or {}
    if not isinstance(request_payload, dict):
        request_payload = {}

    raw_request = request_payload.get("raw_request") or ""
    raw_request_snippet = str(raw_request)[:RAW_REQUEST_SNIPPET_MAX_LEN]

    risk_score = pipeline_output.get("risk_score")
    if not isinstance(risk_score, int):
        risk_score = 0

    audit_entry = {
        "decision": decision,
        "decision_display": get_decision_display(decision),
        "risk_score": risk_score,
        "risk_level": pipeline_output.get("risk_level") or "HIGH",
        "action_type": request_payload.get("action_type") or "UNKNOWN",
        "vendor_name": request_payload.get("vendor_name") or "UNKNOWN",
        "agent_id": request_payload.get("agent_id") or "UNKNOWN",
        "raw_request_snippet": raw_request_snippet,
        "reasoning": pipeline_output.get("final_reasoning") or "No reasoning provided",
        "flags_summary": format_flags_summary(risk_flags),
        "telecom_summary": format_telecom_summary(telecom_signals),
        "risk_flags": risk_flags,
        "telecom_signals": telecom_signals,
        "approver_phone": request_payload.get("phone_number") or "",
        "timestamp": _utc_now_iso(),
    }

    return audit_entry
