"""
AgentGuard - Unified configuration.

Single source of truth for environment variables shared across every layer:
LLM core (Amer), CAMARA infra (Ayham), decision/audit (Noor). Do not split.

Usage: `import config` then read attributes directly, or call
`config.require(*names)` at startup to fail loudly instead of mysteriously later.
"""
import os

from dotenv import load_dotenv

load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
LOW_RISK_MAX = 3
MEDIUM_RISK_MAX = 6


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")





NOKIA_RAPIDAPI_HOST = os.getenv("NOKIA_RAPIDAPI_HOST", "network-as-code.nokia.rapidapi.com")
NOKIA_API_KEY = os.getenv("NOKIA_API_KEY")





NUMBER_VERIFICATION_MODE = os.getenv("NUMBER_VERIFICATION_MODE", "cached").lower()


CACHED_NUMBER_VERIFICATION_RESPONSE = {
    "verified": True,
    "verification_method": "cached_fallback",
}


AUDIT_LOG_TABLE = os.getenv("AUDIT_LOG_TABLE", "audit_logs")

_supabase_client = None


def get_supabase_client():
    """
    Returns a lazily-initialized, shared Supabase client.

    Returns None (instead of raising) if credentials are missing or the
    supabase-py library can't be imported, so the rest of the system can
    apply its own fail-safe behavior instead of crashing at import time.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        print(
            "[config] WARNING: SUPABASE_URL / SUPABASE_KEY not set. "
            "Supabase calls will fail over to fail-safe behavior."
        )
        return None

    try:
        from supabase import create_client

        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        print(f"[config] WARNING: Could not create Supabase client: {e}")
        return None


def confirm_connection():
    """
    Confirm the Supabase connection works by running a simple query against
    the audit_logs table. Prints a clear pass/fail message and never raises.
    """
    client = get_supabase_client()
    if client is None:
        print("[config] Connection check skipped: no Supabase client available.")
        return False

    try:
        client.table(AUDIT_LOG_TABLE).select("*").limit(1).execute()
        print(f"[config] Connected to Supabase. '{AUDIT_LOG_TABLE}' table is reachable.")
        return True
    except Exception as e:
        print(f"[config] Connection check failed: {e}")
        return False


def require(*names):
    """Call this at startup to fail loudly instead of mysteriously later."""
    missing = [n for n in names if not globals().get(n)]
    if missing:
        raise RuntimeError(f"Missing required config values: {', '.join(missing)}. Check your .env file.")


if __name__ == "__main__":
    confirm_connection()