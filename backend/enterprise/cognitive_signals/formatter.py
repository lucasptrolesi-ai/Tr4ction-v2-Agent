"""
Cognitive UX Formatter
======================

Transforms risk/governance outputs into a compact, mobile-first payload for
frontend consumption. Keeps language short and executive.

Payload shape:
{
    "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
    "strategic_alert": str | None,
    "blocking_reason": str | None,
    "violated_dependencies": list[str] | None,
    "learning_feedback": str | None,
}

Notes:
- No business rules are changed; this only formats already computed signals.
- Texts are intentionally short and free of jargon.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class CognitiveUXFormatter:
    """Formats governance/risk outputs into the Phase 3 cognitive payload."""

    MAX_ALERT_LEN = 140
    MAX_FEEDBACK_LEN = 180

    # Language tone templates (Phase 4)
    TONE_VARIANTS = {
        "consultative": {
            "alert_prefix": "Revisar",
            "feedback_prefix": "Considere",
        },
        "educational": {
            "alert_prefix": "Vamos revisar",
            "feedback_prefix": "Dica",
        },
        "executive": {
            "alert_prefix": "Atenção",
            "feedback_prefix": "Ação",
        },
        "technical": {
            "alert_prefix": "Validação",
            "feedback_prefix": "Requisito",
        },
    }

    def build(
        self,
        *,
        risk_result: Optional[Dict[str, Any]] = None,
        governance_results: Optional[List[Dict[str, Any]]] = None,
        blocking_enabled: bool = False,
        language_tone: str = "consultative",
    ) -> Optional[Dict[str, Any]]:
        """Return standardized cognitive_signals payload or None if no data."""

        if not risk_result and not governance_results:
            return None

        level = self._normalize_risk_level(risk_result)
        alert = self._strategic_alert(risk_result, language_tone)
        violated = self._violated_dependencies(risk_result)
        feedback = self._learning_feedback(risk_result, language_tone)
        blocking_reason = self._blocking_reason(risk_result) if blocking_enabled else None

        payload = {
            "risk_level": level,
            "strategic_alert": alert,
            "blocking_reason": blocking_reason,
            "violated_dependencies": violated if violated else None,
            "learning_feedback": feedback,
        }
        return payload

    def _normalize_risk_level(self, risk_result: Optional[Dict[str, Any]]) -> str:
        level = (risk_result or {}).get("overall_risk")
        normalized = (level or "low").upper()
        if normalized not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            return "LOW"
        return normalized

    def _strategic_alert(self, risk_result: Optional[Dict[str, Any]], language_tone: str = "consultative") -> Optional[str]:
        if not risk_result:
            return None

        red_flags = risk_result.get("red_flags") or []
        if red_flags and len(red_flags) > 0:
            first = red_flags[0]
            if isinstance(first, dict):
                msg = first.get("message") or first.get("suggestion") or first.get("type")
                if msg:
                    return self._trim(msg, self.MAX_ALERT_LEN)

        recommendation = risk_result.get("recommendation")
        if recommendation:
            return self._trim(recommendation, self.MAX_ALERT_LEN)

        overall = risk_result.get("overall_risk")
        if overall in {"high", "critical"}:
            tone_config = self.TONE_VARIANTS.get(language_tone, self.TONE_VARIANTS["consultative"])
            prefix = tone_config["alert_prefix"]
            return f"{prefix} entrega antes de avançar"

        return None

    def _violated_dependencies(self, risk_result: Optional[Dict[str, Any]]) -> List[str]:
        deps: List[str] = []
        if not risk_result:
            return deps

        red_flags = risk_result.get("red_flags") or []
        if not isinstance(red_flags, list):
            return deps

        for flag in red_flags:
            if not isinstance(flag, dict):
                continue
            violated = flag.get("violated_dependencies") or []
            if isinstance(violated, list):
                for dep in violated:
                    if isinstance(dep, str) and dep.strip():
                        deps.append(dep)

        # Deduplicate while keeping order
        seen = set()
        unique = []
        for dep in deps:
            if dep not in seen:
                unique.append(dep)
                seen.add(dep)
        return unique

    def _learning_feedback(self, risk_result: Optional[Dict[str, Any]], language_tone: str = "consultative") -> Optional[str]:
        if not risk_result:
            return None

        # Tenta extrair de suggestions dos red_flags primeiro
        red_flags = risk_result.get("red_flags") or []
        if isinstance(red_flags, list) and len(red_flags) > 0:
            first = red_flags[0]
            if isinstance(first, dict):
                suggestion = first.get("suggestion") or first.get("recommendation")
                if suggestion:
                    return self._trim(suggestion, self.MAX_FEEDBACK_LEN)

        recommendations = risk_result.get("recommendations") or []
        if isinstance(recommendations, list) and len(recommendations) > 0:
            first_rec = recommendations[0]
            if isinstance(first_rec, str) and first_rec.strip():
                return self._trim(first_rec, self.MAX_FEEDBACK_LEN)

        summary = risk_result.get("summary") or risk_result.get("insight")
        if summary and isinstance(summary, str):
            return self._trim(summary, self.MAX_FEEDBACK_LEN)

        return None

    def _blocking_reason(self, risk_result: Optional[Dict[str, Any]]) -> Optional[str]:
        if not risk_result:
            return None

        overall = risk_result.get("overall_risk")
        if overall in {"high", "critical"}:
            return "Alinhar com premissas antes de avançar (informativo)."
        return None

    def _trim(self, text: Optional[str], limit: int) -> Optional[str]:
        if not text:
            return None
        stripped = text.strip()
        if len(stripped) <= limit:
            return stripped
        return stripped[: limit - 1].rstrip() + "…"
