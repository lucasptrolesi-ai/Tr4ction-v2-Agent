"""
Cognitive Signals Generator
=============================

Gera sinais estruturados para o FRONTEND, sem quebrar UI existente.

Sinais são campos OPCIONAIS em payloads que ajudam UX cognitiva:

1. RISK_LEVEL: "low" | "medium" | "high" | "critical"
   → Frontend mostra icon/cor diferente

2. ALERT_MESSAGE: String legível
   → "Resposta genérica - seja mais específico"

3. NEXT_STEP_HINT: String
   → "Próximo: Descrever seu ICP"

4. REASONING_SUMMARY: String
   → "Por que isso é importante: ICP define seu go-to-market..."

5. CONFIDENCE_SCORE: 0.0-1.0
   → "Confiança no entendimento: 68%"

6. COHERENCE_ISSUES: List[str]
   → ["Contradiz resposta anterior em Persona"]

IMPORTANTE:
- Não altera contratos existentes
- Apenas adiciona campos opcionais
- Frontend ignora se não usar
- Zero impacto em compatibilidade
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """Tipos de sinais."""
    RISK_LEVEL = "risk_level"
    ALERT = "alert"
    NEXT_STEP = "next_step"
    REASONING = "reasoning"
    CONFIDENCE = "confidence"
    COHERENCE = "coherence"


@dataclass
class CognitiveSignal:
    """Um sinal individual."""
    
    signal_type: SignalType
    value: Any
    severity: Optional[str] = None  # low, medium, high
    actionable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.signal_type.value,
            "value": self.value,
            "severity": self.severity,
            "actionable": self.actionable,
        }


@dataclass
class CognitiveSignalSet:
    """Conjunto de sinais para uma resposta."""
    
    risk_level: Optional[str] = None  # low, medium, high, critical
    alert_message: Optional[str] = None
    next_step_hint: Optional[str] = None
    reasoning_summary: Optional[str] = None
    confidence_score: Optional[float] = None  # 0.0-1.0
    coherence_issues: List[str] = field(default_factory=list)
    
    # Metadados
    generated_at: str = field(default_factory=lambda: __import__('datetime').datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para adicionar ao payload."""
        return {
            "cognitive_signals": {
                "risk_level": self.risk_level,
                "alert_message": self.alert_message,
                "next_step_hint": self.next_step_hint,
                "reasoning_summary": self.reasoning_summary,
                "confidence_score": round(self.confidence_score, 2) if self.confidence_score else None,
                "coherence_issues": self.coherence_issues,
                "generated_at": self.generated_at,
            }
        }


class CognitiveSignalGenerator:
    """Gera sinais para melhorar UX cognitiva."""
    
    def __init__(self):
        logger.info("✓ Cognitive Signal Generator initialized")
    
    def generate_signals_for_response(
        self,
        template_key: str,
        field_key: str,
        value: str,
        risk_assessment: Optional[Dict[str, Any]] = None,
        governance_violations: Optional[List[Dict[str, Any]]] = None,
        coherence_issues: Optional[List[str]] = None,
        related_fields_context: Optional[Dict[str, Any]] = None,
    ) -> CognitiveSignalSet:
        """
        Gera sinais para uma resposta de campo.
        
        Args:
            template_key: Ex: "persona_01"
            field_key: Ex: "pain_points"
            value: Resposta do founder
            risk_assessment: Dict com risk_level, trust_score, etc
            governance_violations: Lista de violações detectadas
            coherence_issues: Lista de inconsistências
            related_fields_context: Contexto de campos relacionados
        
        Returns:
            CognitiveSignalSet com sinais gerados
        """
        
        signals = CognitiveSignalSet()
        
        # 1. Risk level (baseado em risk_assessment)
        if risk_assessment:
            signals.risk_level = risk_assessment.get("overall_risk", "low")
        
        # 2. Alert message (baseado em violations/risk)
        if governance_violations and len(governance_violations) > 0:
            violation = governance_violations[0]
            signals.alert_message = violation.get("message", "Possível problema detectado")
        elif risk_assessment and risk_assessment.get("overall_risk") in ["high", "critical"]:
            signals.alert_message = self._generate_alert_from_risk(risk_assessment)
        
        # 3. Next step hint
        signals.next_step_hint = self._generate_next_step(template_key, field_key)
        
        # 4. Reasoning summary
        signals.reasoning_summary = self._generate_reasoning(template_key, field_key)
        
        # 5. Confidence score
        if risk_assessment:
            signals.confidence_score = risk_assessment.get("trust_score", 0.5)
        
        # 6. Coherence issues
        if coherence_issues:
            signals.coherence_issues = coherence_issues
        
        return signals
    
    def generate_signals_for_template(
        self,
        template_key: str,
        completed_fields: Dict[str, Any],
        risk_assessment: Optional[Dict[str, Any]] = None,
        governance_violations: Optional[List[Dict[str, Any]]] = None,
    ) -> CognitiveSignalSet:
        """
        Gera sinais para um template completo.
        """
        
        signals = CognitiveSignalSet()
        
        # Risk level geral
        if risk_assessment:
            signals.risk_level = risk_assessment.get("overall_risk", "low")
            signals.confidence_score = risk_assessment.get("trust_score", 0.5)
        
        # Conta violations
        if governance_violations:
            violation_types = set(v.get("rule_type") for v in governance_violations)
            if "required" in violation_types:
                signals.alert_message = "Há campos obrigatórios não preenchidos"
            elif "pattern" in violation_types:
                signals.alert_message = "Algumas respostas são muito genéricas"
        
        # Next step
        signals.next_step_hint = f"Próximo: Revisar suas respostas e avançar para template seguinte"
        
        # Reasoning
        signals.reasoning_summary = (
            f"Você preencheu {len(completed_fields)} campos do template {template_key}. "
            "Essas informações ajudam o sistema a gerar recomendações mais precisas."
        )
        
        return signals
    
    def _generate_alert_from_risk(self, risk_assessment: Dict[str, Any]) -> str:
        """Gera mensagem de alerta baseado em risk assessment."""
        
        red_flags = risk_assessment.get("red_flags", [])
        
        if not red_flags:
            return "Resposta precisa de revisão"
        
        flag = red_flags[0]
        flag_type = flag.get("type")
        
        if flag_type == "generic_response":
            return "Sua resposta é muito genérica. Seja mais específico e concreto."
        elif flag_type == "coherence_violation":
            return "Isso contradiz uma resposta anterior. Revise para coerência."
        elif flag_type == "frequent_changes":
            return "Você mudou essa resposta múltiplas vezes. Talvez converse com um mentor."
        
        return "Possível problema detectado. Revise sua resposta."
    
    def _generate_next_step(self, template_key: str, field_key: str) -> str:
        """Gera hint de próximo passo."""
        
        # Mapeamento simples (pode ser expandido)
        next_steps = {
            "icp_01": "Próximo: Descrever a Persona ideal do seu cliente",
            "persona_01": "Próximo: Analisar o Market Size",
            "market_01": "Próximo: Definir sua estratégia de Go-to-Market",
        }
        
        return next_steps.get(template_key, "Continue preenchendo os próximos campos")
    
    def _generate_reasoning(self, template_key: str, field_key: str) -> str:
        """Gera reasoning summary (por quê isso importa)."""
        
        reasoning_map = {
            "icp_01": {
                "company_size": "O tamanho da empresa define seu poder de compra e ciclo de venda.",
                "industry": "A indústria afeta as dores, orçamentos e ciclos de decisão.",
                "budget": "O orçamento disponível determina seu positioning de preço.",
            },
            "persona_01": {
                "pain_points": "Os pain points são o gatilho para que alguém compre sua solução.",
                "goals": "Os goals determinam se sua proposta de valor realmente alinha.",
            },
        }
        
        return reasoning_map.get(template_key, {}).get(field_key, "")
    
    def merge_signals_into_payload(
        self,
        original_payload: Dict[str, Any],
        signals: CognitiveSignalSet,
    ) -> Dict[str, Any]:
        """
        Mescla sinais no payload original SEM quebrar contrato.
        
        Adiciona 'cognitive_signals' field opcional.
        """
        
        payload = original_payload.copy()
        payload.update(signals.to_dict())
        
        return payload
