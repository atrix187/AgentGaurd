"""
CAMARA Device Swap check.
Real SDK calls: client.device_swap.check(phone_number=..., max_age=...)
                client.device_swap.retrieve_date(phone_number=...)
"""
import logging
from camara._client import get_client

logger = logging.getLogger("agentguard.camara.device_swap")

DEFAULT_MAX_AGE_HOURS = 240


def check_device_swap(phone_number: str) -> dict:
    """
    Returns:
        {
          "device_swapped": bool,
          "swap_date": str | None,
        }
    """
    try:
        client = get_client()

        swap_result = client.device_swap.check(
            phone_number=phone_number,
            max_age=DEFAULT_MAX_AGE_HOURS,
        )

        swap_date = None
        if swap_result.swapped:
            date_result = client.device_swap.retrieve_date(phone_number=phone_number)
            if date_result.latest_device_change:
                swap_date = date_result.latest_device_change.isoformat()

        return {
            "device_swapped": bool(swap_result.swapped),
            "swap_date": swap_date,
        }

    except Exception as e:
        logger.error(f"Device Swap check failed for {phone_number}: {e}")
        return {"device_swapped": False, "swap_date": None}
