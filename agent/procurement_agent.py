from typing import Any

DEMO_VENDORS = ("Al Fardan Supplies", "Gulf Tech Corp", "ShadyVendor LLC")


class DummyProcurementAgent:

    def receive_request(
        self, raw_request: str, agent_id: str, phone_number: str
    ) -> dict[str, Any]:
        vendor_name = next(
            (vendor for vendor in DEMO_VENDORS if vendor.lower() in raw_request.lower()),
            "Unknown Vendor",
        )
        request_payload = {
            "agent_id": agent_id,
            "action_type": "vendor_bank_detail_change",
            "raw_request": raw_request,
            "vendor_name": vendor_name,
            "phone_number": phone_number,
        }
        print("Dummy Procurement Agent received request:", raw_request)
        print("Routing request to AgentGuard pipeline.")
        return request_payload
