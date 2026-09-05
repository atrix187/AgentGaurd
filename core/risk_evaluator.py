import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from config import (
    GEMINI_FALLBACK_MODEL,
    GOOGLE_API_KEY,
    GROQ_API_KEY,
    GROQ_MODEL,
    get_supabase_client,
)
from core.prompts import RISK_EVALUATOR_SYSTEM_PROMPT, RISK_EVALUATOR_USER_TEMPLATE


class RiskEvaluator:
    def __init__(self) -> None:
        self.llm = (
            ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0)
            if GROQ_API_KEY
            else None
        )
        self.supabase = get_supabase_client()

    def get_vendor_history(self, vendor_name: str) -> dict[str, Any] | None:
        """Read a vendor record, treating unavailable Supabase as unknown."""
        if not self.supabase:
            return None
        try:
            response = (
                self.supabase.table("vendors")
                .select(
                    "name,relationship_months,bank_detail_changes,"
                    "last_bank_change_date,total_volume_usd"
                )
                .eq("name", vendor_name)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception:
            return None

    def evaluate(self, request_payload: dict[str, Any]) -> dict[str, Any]:
        history = self.get_vendor_history(request_payload["vendor_name"])
        vendor_status = "established" if history else "new or unknown"
        user_message = RISK_EVALUATOR_USER_TEMPLATE.format(
            raw_request=request_payload["raw_request"],
            vendor_history=json.dumps(history or {"status": "unknown"}),
            vendor_status=vendor_status,
        )
        try:
            content = self._invoke(user_message)
            assessment = self._parse_json_response(content)
            self._validate_assessment(assessment)
            return assessment
        except Exception as e:
            import traceback
            print(f"\n[RiskEvaluator] LLM call failed: {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._safe_default()

    @staticmethod
    def _parse_json_response(content: str) -> dict[str, Any]:
        """Parse JSON-only output, accepting an accidental Markdown code fence."""
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else ""
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("LLM response contains no JSON object")
        parsed = json.loads(cleaned[start : end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("LLM response is not a JSON object")
        return parsed

    def _invoke(self, user_message: str) -> str:
        messages = [SystemMessage(RISK_EVALUATOR_SYSTEM_PROMPT), HumanMessage(user_message)]
        if self.llm:
            try:
                return self.llm.invoke(messages).content
            except Exception:
                if not GOOGLE_API_KEY:
                    raise
        if GOOGLE_API_KEY:
            from langchain_google_genai import ChatGoogleGenerativeAI

            fallback = ChatGoogleGenerativeAI(
                model=GEMINI_FALLBACK_MODEL,
                api_key=GOOGLE_API_KEY,
                temperature=0,
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "risk_score": {"type": "integer", "minimum": 1, "maximum": 10},
                        "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                        "reasoning": {"type": "string"},
                        "flags": {"type": "array", "items": {"type": "string"}},
                        "recommended_action": {
                            "type": "string",
                            "enum": ["AUTO_APPROVE", "STEP_UP_VERIFICATION", "BLOCK"],
                        },
                    },
                    "required": [
                        "risk_score",
                        "risk_level",
                        "reasoning",
                        "flags",
                        "recommended_action",
                    ],
                },
            )
            response = fallback.invoke(messages)
            return self._response_text(response.content)
        raise RuntimeError("No LLM API key configured")

    @staticmethod
    def _response_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                item.get("text", "") for item in content if isinstance(item, dict)
            )
        raise ValueError("LLM response did not contain text")

    @staticmethod
    def _validate_assessment(assessment: dict[str, Any]) -> None:
        required = {"risk_score", "risk_level", "reasoning", "flags", "recommended_action"}
        if set(assessment) != required or not isinstance(assessment["risk_score"], int):
            raise ValueError("Invalid LLM assessment")
        if not 1 <= assessment["risk_score"] <= 10:
            raise ValueError("Risk score outside valid range")
        expected_level = "LOW" if assessment["risk_score"] <= 3 else "MEDIUM" if assessment["risk_score"] <= 6 else "HIGH"
        if assessment["risk_level"] != expected_level:
            raise ValueError("Risk level does not match score")
        if assessment["recommended_action"] not in {
            "AUTO_APPROVE",
            "STEP_UP_VERIFICATION",
            "BLOCK",
        } or not isinstance(assessment["reasoning"], str) or not isinstance(assessment["flags"], list):
            raise ValueError("Invalid assessment fields")

    @staticmethod
    def _safe_default() -> dict[str, Any]:
        return {
            "risk_score": 8,
            "risk_level": "HIGH",
            "reasoning": "Risk evaluation could not be parsed; blocking safely.",
            "flags": ["RISK_EVALUATION_FAILURE"],
            "recommended_action": "BLOCK",
        }
