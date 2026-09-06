"""
CAMARA Device Status check.
Real SDK call: client.device_status.check_connectivity(device={"phone_number": ...})
Response connectivity_status is one of: CONNECTED_DATA, CONNECTED_SMS, NOT_CONNECTED
"""
import logging
from camara._client import get_client

logger = logging.getLogger("agentguard.camara.device_status")


def check_device_status(phone_number: str) -> dict:
    """
    Returns:
        {
          "reachable": bool,
          "status": str,   # CONNECTED_DATA | CONNECTED_SMS | NOT_CONNECTED | UNKNOWN
        }
    """
    try:
        client = get_client()

        result = client.device_status.check_connectivity(
            device={"phone_number": phone_number},
        )

        status = result.connectivity_status
        reachable = status in ("CONNECTED_DATA", "CONNECTED_SMS")

        return {"reachable": reachable, "status": status}

    except Exception as e:
        logger.error(f"Device Status check failed for {phone_number}: {e}")
        return {"reachable": False, "status": "UNKNOWN"}
