"""
decision/decision_engine.py
-----------------------------
The main entry point for AgentGuard's decision layer. Takes Amer's raw
LangGraph pipeline output, validates/sanitizes it, writes an audit
entry, and returns the clean verdict dict Tariq's frontend consumes.

Phase 4 of Noor's spec.
"""

from datetime import datetime, timezone

from audit.audit_formatter import (
    build_audit_entry,
    format_flags_summary,
    format_telecom_summary,
    get_decision_display,
)
from audit.audit_logger import AuditLogger

VALID_DECISIONS = ("APPROVED", "STEP_UP", "BLOCKED")


class DecisionEngine:
    def __init__(self, audit_logger=None):


        self.audit_logger = audit_logger if audit_logger is not None else AuditLogger()

    def _sanitize(self, pipeline_output):
        """
        Fail-safe input validation. Fills any missing field with a safe
        default and defaults an unrecognized/missing decision to
        BLOCKED. Never raises, regardless of what Amer's pipeline sends.
        """
        pipeline_output = pipeline_output if isinstance(pipeline_output, dict) else {}

        decision = pipeline_output.get("final_decision")
        if decision not in VALID_DECISIONS:
            decision = "BLOCKED"

        risk_score = pipeline_output.get("risk_score")
        if not isinstance(risk_score, int):
            risk_score = 0

        risk_flags = pipeline_output.get("risk_flags")
        if not isinstance(risk_flags, list):
            risk_flags = []

        telecom_signals = pipeline_output.get("telecom_signals")
        if not isinstance(telecom_signals, dict):
            telecom_signals = {}

        request_payload = pipeline_output.get("request_payload")
        if not isinstance(request_payload, dict):
            request_payload = {}

        sanitized = {
            "final_decision": decision,
            "final_reasoning": pipeline_output.get("final_reasoning") or "No reasoning provided",
            "risk_score": risk_score,
            "risk_level": pipeline_output.get("risk_level") or "HIGH",
            "risk_flags": risk_flags,
            "telecom_signals": {
                "sim_swap": telecom_signals.get("sim_swap"),
                "device_status": telecom_signals.get("device_status"),
                "device_swap": telecom_signals.get("device_swap"),
                "number_verification": telecom_signals.get("number_verification"),
            },
            "request_payload": {
                "agent_id": request_payload.get("agent_id") or "UNKNOWN",
                "action_type": request_payload.get("action_type") or "UNKNOWN",
                "raw_request": request_payload.get("raw_request") or "",
                "vendor_name": request_payload.get("vendor_name") or "UNKNOWN",
                "phone_number": request_payload.get("phone_number") or "",
            },
        }

        return sanitized

    def process(self, pipeline_output):
        """
        Main entry point (Phase 4, step 2).

        1. Validates/sanitizes Amer's raw pipeline output
        2. Builds the audit entry
        3. Writes it to the audit_logs table via AuditLogger.log
        4. Returns the final response dict for Tariq's frontend

        Never raises — a malformed pipeline_output degrades to a
        BLOCKED, low-confidence response rather than crashing.
        """
        try:
            sanitized = self._sanitize(pipeline_output)
        except Exception as e:
            print(f"[decision_engine] Sanitization failed unexpectedly ({e}). Defaulting to BLOCKED.")
            sanitized = self._sanitize({})

        audit_entry = build_audit_entry(sanitized)

        try:
            log_id = self.audit_logger.log(sanitized)
        except Exception as e:
            print(f"[decision_engine] Logging failed unexpectedly: {e}")
            log_id = None

        response = {
            "decision": audit_entry["decision"],
            "decision_display": audit_entry["decision_display"],
            "risk_score": audit_entry["risk_score"],
            "risk_level": audit_entry["risk_level"],
            "reasoning": audit_entry["reasoning"],
            "flags_summary": audit_entry["flags_summary"],
            "telecom_summary": audit_entry["telecom_summary"],
            "vendor_name": audit_entry["vendor_name"],
            "timestamp": audit_entry["timestamp"],
            "audit_entry": audit_entry,
            "log_id": log_id,
        }

        return response

    def get_audit_trail(self, limit=20):
        """
        Phase 4, step 4: returns the most recent audit entries.
        Tariq imports this to render the audit trail view.
        """
        return self.audit_logger.get_recent_logs(limit)

    def get_vendor_history_trail(self, vendor_name):
        """
        Phase 4, step 5: returns the full audit history for a single
        vendor. Used in the demo to show attack patterns (e.g. a vendor
        suddenly requesting a bank detail change after a SIM swap).
        """
        return self.audit_logger.get_logs_by_vendor(vendor_name)
