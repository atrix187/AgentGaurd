"""
AgentGuard - Infra test harness.

Run this to test everything: Supabase connectivity, all 3 simple CAMARA
checks (SIM Swap, Device Status, Device Swap), and Number Verification.

Usage:
    python scripts/infra_test.py             # runs everything, "cached" mode by default
    python scripts/infra_test.py --live      # runs Number Verification against the real
                                             # Simulator API instead of the cached mock
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from supabase import create_client


def test_supabase():
    print("\n=== Supabase ===")
    config.require("SUPABASE_URL", "SUPABASE_KEY")
    supa = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

    vendors = supa.table("vendors").select("*").execute()
    print(f"vendors table: {len(vendors.data)} rows")
    for v in vendors.data:
        print(f"  - {v['name']}")
    assert len(vendors.data) == 3, "Expected exactly 3 seeded vendor rows"

    test_row = {
        "decision": "approve",
        "decision_display": "Approved (test insert from main.py)",
        "risk_score": 10,
        "risk_level": "low",
        "action_type": "test",
        "vendor_name": "Al Fardan Supplies",
        "agent_id": "test-harness",
        "raw_request_snippet": "main.py connectivity test",
        "reasoning": "verifying audit_logs accepts inserts",
        "flags_summary": "none",
        "telecom_summary": "none",
        "risk_flags": {},
        "telecom_signals": {},
        "approver_phone": "+99999991000",
    }
    insert_result = supa.table("audit_logs").insert(test_row).execute()
    print(f"audit_logs insert: OK (id={insert_result.data[0]['id']})")




SIMULATOR_NUMBERS = {
    "+99999991000": "swapped=true (SIM+device) / CONNECTED_SMS / verify=true  -> 'attack case'",
    "+99999991001": "swapped=false (SIM+device) / CONNECTED_DATA / verify=false -> 'baseline'",
    "+99999991002": "device status only: NOT_CONNECTED",
}


def test_simple_camara_checks():
    from camara.sim_swap import check_sim_swap
    from camara.device_status import check_device_status
    from camara.device_swap import check_device_swap

    print("\n=== CAMARA simple checks (all simulator numbers) ===")
    for number, meaning in SIMULATOR_NUMBERS.items():
        print(f"\n--- {number}  ({meaning}) ---")
        print("SIM Swap:      ", check_sim_swap(number))
        print("Device Status: ", check_device_status(number))
        print("Device Swap:   ", check_device_swap(number))


def test_number_verification():
    from camara.number_verification import trigger_number_verification

    print(f"\n=== Number Verification (mode={config.NUMBER_VERIFICATION_MODE}) ===")

    for number in ("+99999991000", "+99999991001"):
        print(f"{number}: ", trigger_number_verification(number))


if __name__ == "__main__":
    if "--live" in sys.argv:
        config.NUMBER_VERIFICATION_MODE = "live"

    test_supabase()
    test_simple_camara_checks()
    test_number_verification()