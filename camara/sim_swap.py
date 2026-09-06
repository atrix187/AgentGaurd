"""
CAMARA SIM Swap check.
Real SDK call: client.sim_swap.check(phone_number=..., max_age=...)
"""
import logging
from camara._client import get_client

logger = logging.getLogger("agentguard.camara.sim_swap")

DEFAULT_MAX_AGE_HOURS = 240


def check_sim_swap(phone_number: str) -> dict:
    """
    Returns:
        {
          "swapped": bool,
          "swap_date": str | None,
          "days_since_swap": int | None,
        }
    """
    try:
        client = get_client()

        swap_result = client.sim_swap.check(
            phone_number=phone_number,
            max_age=DEFAULT_MAX_AGE_HOURS,
        )

        swap_date = None
        days_since_swap = None

        if swap_result.swapped:
            date_result = client.sim_swap.retrieve_date(phone_number=phone_number)
            if date_result.latest_sim_change:
                swap_date = date_result.latest_sim_change.isoformat()
                import datetime
                delta = datetime.datetime.now(datetime.timezone.utc) - date_result.latest_sim_change
                days_since_swap = delta.days

        return {
            "swapped": bool(swap_result.swapped),
            "swap_date": swap_date,
            "days_since_swap": days_since_swap,
        }

    except Exception as e:
        logger.error(f"SIM Swap check failed for {phone_number}: {e}")
        return {"swapped": False, "swap_date": None, "days_since_swap": None}
