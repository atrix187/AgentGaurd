"""
audit/audit_logger.py
-----------------------
Writes decisions to the `audit_logs` Supabase table and reads them
back for the frontend / demo.

Phase 3 of Noor's spec.
"""

import json

from config import get_supabase_client, AUDIT_LOG_TABLE
from audit.audit_formatter import build_audit_entry


JSONB_FIELDS = ("risk_flags", "telecom_signals")


class AuditLogger:
    def __init__(self, client=None):


        self.client = client if client is not None else get_supabase_client()

    def _serialize_jsonb_fields(self, entry):
        """Returns a copy of entry with jsonb fields JSON-encoded as strings."""
        row = dict(entry)
        for field in JSONB_FIELDS:
            if field in row:
                try:
                    row[field] = json.dumps(row[field])
                except (TypeError, ValueError):
                    row[field] = json.dumps(str(row[field]))
        return row

    def log(self, pipeline_output):
        """
        Phase 3, step 2: builds the audit entry from Amer's pipeline
        output, serializes jsonb fields, and inserts it into the
        audit_logs table.

        Returns the new row's log_id (int) on success, or None if the
        insert failed or no Supabase client is available. Never raises
        — per the fail-safe rules, prints the entry to console instead.
        """
        entry = build_audit_entry(pipeline_output)

        if self.client is None:
            print("[audit_logger] No Supabase client available. Audit entry:")
            print(json.dumps(entry, default=str, indent=2))
            return None

        row = self._serialize_jsonb_fields(entry)

        try:
            result = self.client.table(AUDIT_LOG_TABLE).insert(row).execute()
            data = getattr(result, "data", None)
            if data:
                return data[0].get("id")
            return None
        except Exception as e:
            print(f"[audit_logger] Supabase insert failed ({e}). Audit entry:")
            print(json.dumps(entry, default=str, indent=2))
            return None

    def get_recent_logs(self, limit=20):
        """
        Phase 3, step 3: fetches the most recent audit entries ordered
        by timestamp descending. Returns [] on any failure — never
        raises. Tariq calls this to display the audit trail.
        """
        if self.client is None:
            print("[audit_logger] No Supabase client available. Returning empty list.")
            return []

        try:
            result = (
                self.client.table(AUDIT_LOG_TABLE)
                .select("*")
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"[audit_logger] Supabase fetch (recent) failed: {e}")
            return []

    def get_logs_by_vendor(self, vendor_name):
        """
        Phase 3, step 4: fetches all audit entries for a specific vendor,
        most recent first. Returns [] on any failure — never raises.
        """
        if self.client is None:
            print("[audit_logger] No Supabase client available. Returning empty list.")
            return []

        try:
            result = (
                self.client.table(AUDIT_LOG_TABLE)
                .select("*")
                .eq("vendor_name", vendor_name)
                .order("timestamp", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"[audit_logger] Supabase fetch (by vendor) failed: {e}")
            return []
