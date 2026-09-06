"""
CAMARA Number Verification.

REALITY CHECK (confirmed against the actual Nokia dashboard, Simulator plan):
Despite the spec doc describing a full 3-legged OAuth redirect flow, the
Simulator plan's phoneNumberVerify-NV-V2 endpoint needs NO additional
authorization beyond your normal X-RapidAPI-Key - it's a direct POST with
just {"phoneNumber": ...} (+ optional nullable "credential" field, which
appears to only matter for the live/production flow, not simulator).

Simulator behavior (confirmed from the dashboard's own example bodies):
    +99999991000 -> verified = true
    +99999991001 -> verified = false

So in sandbox, trigger_number_verification() below just calls the API
directly - no redirect_uri, no ngrok, no manual code-paste step needed.

If/when the team moves off Simulator mode to a real billing account, the
real 3-legged OAuth flow (device opens a URL over mobile data, consents,
redirects back with a code) becomes necessary. That path isn't built here
since it's out of scope until billing is set up - flag it to Ghaith if the
team needs it before the demo.
"""
import logging
from camara._client import get_client
import config

logger = logging.getLogger("agentguard.camara.number_verification")




SIMULATOR_VERIFIED = {
    "+99999991000": True,
    "+99999991001": False,
}


def trigger_number_verification(phone_number: str) -> dict:
    """
    FIXED SIGNATURE - this is what tools/tool_stubs.py imports and what
    Amer's pipeline calls. Do not change this signature.

    In "cached" mode: always returns the pre-recorded response, no API call.
    In "live" mode: calls the real Simulator endpoint directly.

    Returns:
        {
          "verified": bool,
          "verification_method": str,
        }
    """
    if config.NUMBER_VERIFICATION_MODE == "cached":
        verified = SIMULATOR_VERIFIED.get(
            phone_number, config.CACHED_NUMBER_VERIFICATION_RESPONSE["verified"]
        )
        return {
            "verified": verified,
            "verification_method": "simulator_cached",
        }

    try:
        client = get_client()
        result = client.number_verification.verify_v2(request={"phone_number": phone_number})
        verified = bool(getattr(result, "device_phone_number_verified", False))

        return {
            "verified": verified,
            "verification_method": "simulator_verify",
        }

    except Exception as e:
        logger.error(f"Number Verification failed for {phone_number}: {e}")
        return dict(config.CACHED_NUMBER_VERIFICATION_RESPONSE)
