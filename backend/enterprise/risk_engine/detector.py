"""
Risk Detection & Red Flag System
==================================

Classifica NÍVEL DE RISCO nas decisões do founder:
- Baixo: Decisão confiável, com contexto
- Médio: Alguma incoerência, precisa revisão
- Alto: Red flag claro (contradição, genérico, inconsistência)
- Crítico: Problema que bloqueia avanço (se flag ativa)

IMPORTANTE:
- Funciona como OBSERVER puro - nunca altera fluxo
- Emite sinais estruturados para frontend
- Alimenta AI Mentor com contexto de risco
- Detecta padrões de incoerência

Red Flags detectadas:
1. Resposta genérica (palavras vazias)
2. Contradições com templates relacionados
3. Mudanças frequentes (indecisão)
4. Falta de alignment ICP → Persona
5. Strategy inconsistente ao longo do tempo
"""

from typing import Dict, List, Any, Optional, Literal, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskClassification(str, Enum):
    """Classificação de risco."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RedFlag:
    """Uma bandeira vermelha detectada."""
    
    flag_type: Literal[
        "generic_response",
        "coherence_violation",
        "frequent_changes",
        "missing_alignment",
        "inconsistent_strategy",
        "data_quality",
        "assumption_gap",
        "market_mismatch",
    ]
    severity: RiskClassification
    message: str
    field: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    violated_dependencies: Optional[List[str]] = None
    recommendation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para API."""
        return {
            "type": self.flag_type,
            "severity": self.severity.value,
            "message": self.message,
            "field": self.field,
            "evidence": self.evidence,
            "suggestion": self.suggestion,
            "violated_dependencies": self.violated_dependencies,
            "recommendation": self.recommendation,
        }


@dataclass
class RiskAssessment:
    """Avaliação completa de risco."""
    
    template_key: str
    overall_risk: RiskClassification
    red_flags: List[RedFlag] = field(default_factory=list)
    trust_score: float = 1.0  # 0.0 = não confiável, 1.0 = totalmente confiável
    data_quality: float = 1.0
    coherence_score: float = 1.0
    decision_maturity: Literal["reactive", "considered", "strategic"] = "reactive"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para API."""
        return {
            "template_key": self.template_key,
            "overall_risk": self.overall_risk.value,
            "red_flags": [f.to_dict() for f in self.red_flags],
            "trust_score": round(self.trust_score, 2),
            "data_quality": round(self.data_quality, 2),
            "coherence_score": round(self.coherence_score, 2),
            "decision_maturity": self.decision_maturity,
            "timestamp": self.timestamp.isoformat(),
        }


class RiskDetectionEngine:
    """Motor de detecção de risco."""
    
    # Palavras genéricas = red flag
    GENERIC_WORDS = {
        "aumentar": 2,  # Score de genericidade
        "melhorar": 2,
        "good": 2,
        "better": 2,
        "nice": 2,
        "fazer": 3,
        "coisa": 3,
        "tipo": 2,
        "algo": 2,
        "etc": 3,
    }
    
    # Padrões de coerência esperados
    COHERENCE_RULES = {
        "icp_01.company_size": {
            "must_align_with": {
                "persona_01.occupation": {
                    "small": ["freelancer", "entrepreneur", "cto"],
                    "medium": ["manager", "director", "vp"],
                    "large": ["cfo", "ceo", "vp_operations"],
                },
            }
        },
    }
    
    def __init__(self):
        logger.info("✓ Risk Detection Engine initialized")
    
    def assess_field_response(
        self,
        template_key: str,
        field_key: str,
        value: str,
        related_templates: Optional[Dict[str, Dict]] = None,
    ) -> RiskAssessment:
        """
        Avalia nível de risco de uma resposta de campo.
        
        Args:
            template_key: Ex: "persona_01"
            field_key: Ex: "pain_points"
            value: Valor respondido
            related_templates: Dados de templates relacionados para coerência
        
        Returns:
            RiskAssessment com classificação completa
        """
        
        assessment = RiskAssessment(template_key=template_key)
        
        # 1. Detecta respostas genéricas
        generic_score = self._check_generic_response(value)
        if generic_score > 2.0:
            flag = RedFlag(
                flag_type="generic_response",
                severity=RiskClassification.MEDIUM if generic_score < 4 else RiskClassification.HIGH,
                message="Resposta precisa de mais detalhes",
                field=field_key,
                suggestion="Adicione exemplos concretos do seu contexto",
            )
            assessment.red_flags.append(flag)
            assessment.data_quality *= 0.7
        
        # 2. Valida tamanho da resposta
        if len(value.strip()) < 20:
            flag = RedFlag(
                flag_type="data_quality",
                severity=RiskClassification.MEDIUM,
                message="Resposta muito curta",
                field=field_key,
                suggestion="Expanda com mais contexto",
            )
            assessment.red_flags.append(flag)
            assessment.data_quality *= 0.6
        
        # 3. Valida coerência com templates relacionados
        if related_templates:
            coherence_issues = self._check_coherence(
                template_key, field_key, value, related_templates
            )
            for issue in coherence_issues:
                assessment.red_flags.append(issue)
                assessment.coherence_score *= 0.8
        
        # Calcula risco geral
        assessment = self._compute_overall_risk(assessment)
        
        return assessment
    
    def assess_template_response(
        self,
        template_key: str,
        data: Dict[str, Any],
        previous_versions: Optional[List[Dict[str, Any]]] = None,
        related_templates: Optional[Dict[str, Dict]] = None,
        premises: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessment:
        """
        Avalia risco completo de um template preenchido.
        
        Args:
            template_key: Ex: "persona_01"
            data: Dados preenchidos
            previous_versions: Versões anteriores para detectar mudanças
            related_templates: Dados de templates relacionados
        
        Returns:
            RiskAssessment completo
        """
        
        assessment = RiskAssessment(template_key=template_key)
        
        # 1. Avalia cada campo
        for field_key, value in data.items():
            if isinstance(value, str) and len(value) > 0:
                field_assessment = self.assess_field_response(
                    template_key, field_key, value, related_templates
                )
                assessment.red_flags.extend(field_assessment.red_flags)
        
        # 2. Detecta mudanças frequentes
        if previous_versions and len(previous_versions) > 2:
            change_count = 0
            for prev in previous_versions[-3:]:
                if prev != data:
                    change_count += 1
            
            if change_count >= 2:
                flag = RedFlag(
                    flag_type="frequent_changes",
                    severity=RiskClassification.MEDIUM,
                    message="Revisões múltiplas detectadas",
                    evidence={"recent_changes": change_count},
                    suggestion="Considere validar sua estratégia antes de avançar",
                )
                assessment.red_flags.append(flag)

        # 3. Incoerências com premissas ativas
        if premises:
            premise_flags = self._check_premises_alignment(template_key, data, premises)
            assessment.red_flags.extend(premise_flags)
        
        # 4. Calcula scores finais
        assessment.data_quality = max(0.1, assessment.data_quality)
        assessment.coherence_score = max(0.1, assessment.coherence_score)
        assessment.trust_score = (
            assessment.data_quality * 0.4 + 
            assessment.coherence_score * 0.6
        )
        
        # Determina decision_maturity
        if assessment.trust_score > 0.8:
            assessment.decision_maturity = "strategic"
        elif assessment.trust_score > 0.5:
            assessment.decision_maturity = "considered"
        else:
            assessment.decision_maturity = "reactive"
        
        # Calcula risco geral
        assessment = self._compute_overall_risk(assessment)
        
        return assessment
    
    def _check_generic_response(self, value: str) -> float:
        """
        Calcula score de genericidade (0 = específico, >4 = muito genérico).
        """
        if not value:
            return 5.0
        
        value_lower = value.lower()
        score = 0.0
        
        for word, weight in self.GENERIC_WORDS.items():
            if word in value_lower:
                score += weight
        
        # Penaliza respostas muito curtas
        if len(value) < 30:
            score += 2.0
        
        return score
    
    def _check_coherence(
        self,
        template_key: str,
        field_key: str,
        value: str,
        related_templates: Dict[str, Dict],
    ) -> List[RedFlag]:
        """
        Valida coerência com templates relacionados.
        """
        flags = []
        
        # Exemplo simples: ICP → Persona alignment
        if template_key == "icp_01" and field_key == "company_size":
            if "persona_01" in related_templates:
                persona = related_templates["persona_01"].get("data", {})
                occupation = persona.get("occupation", "").lower()
                
                # Se ICP é "large" mas Persona é "freelancer", é incoerência
                if value.lower() == "large" and "freelancer" in occupation:
                    flags.append(RedFlag(
                        flag_type="coherence_violation",
                        severity=RiskClassification.HIGH,
                        message="ICP e Persona não estão alinhados",
                        evidence={"icp_size": value, "persona_occupation": occupation},
                        suggestion="Revise para garantir coerência estratégica",
                    ))
        
        return flags

    def _check_premises_alignment(
        self,
        template_key: str,
        data: Dict[str, Any],
        premises: Dict[str, Any],
    ) -> List[RedFlag]:
        """Detecta gaps entre decisão atual e premissas ativas."""
        flags: List[RedFlag] = []
        assumptions = premises.get("assumptions", []) if premises else []
        constraints = premises.get("constraints", []) if premises else []

        if not assumptions and not constraints:
            return flags

        # Assumption gap: premissas existem mas decisão não referencia nada relacionado
        filled_fields = [k for k, v in data.items() if v not in (None, "", [], {})]
        if assumptions and len(filled_fields) < max(1, int(len(data) * 0.3)):
            flags.append(
                RedFlag(
                    flag_type="assumption_gap",
                    severity=RiskClassification.MEDIUM,
                    message="Premissas pouco refletidas na entrega",
                    evidence={"filled_fields": filled_fields, "assumptions": assumptions},
                    violated_dependencies=["premises.assumptions"],
                    recommendation="Revisite premissas declaradas e incorpore-as",
                )
            )

        # Market mismatch: se constraint menciona B2B mas campos indicam B2C (heurística simples)
        constraint_text = " ".join(constraints).lower()
        answer_text = " ".join(str(v) for v in data.values() if isinstance(v, str)).lower()
        if "b2b" in constraint_text and "b2c" in answer_text:
            flags.append(
                RedFlag(
                    flag_type="market_mismatch",
                    severity=RiskClassification.HIGH,
                    message="Foco de mercado diverge das restrições",
                    evidence={"constraints": constraints, "answer": answer_text[:120]},
                    violated_dependencies=["premises.constraints"],
                    recommendation="Alinhe ICP ao modelo B2B declarado",
                )
            )

        return flags
    
    def _compute_overall_risk(self, assessment: RiskAssessment) -> RiskAssessment:
        """Computa classificação geral de risco."""
        
        # Conta flags por severity
        critical = sum(1 for f in assessment.red_flags if f.severity == RiskClassification.CRITICAL)
        high = sum(1 for f in assessment.red_flags if f.severity == RiskClassification.HIGH)
        medium = sum(1 for f in assessment.red_flags if f.severity == RiskClassification.MEDIUM)
        
        if critical > 0:
            assessment.overall_risk = RiskClassification.CRITICAL
        elif high > 0:
            assessment.overall_risk = RiskClassification.HIGH
        elif medium > 0:
            assessment.overall_risk = RiskClassification.MEDIUM
        else:
            assessment.overall_risk = RiskClassification.LOW
        
        return assessment
    
    def get_mentoring_focus(self, assessment: RiskAssessment) -> Dict[str, Any]:
        """
        Retorna recomendação de foco para AI Mentor baseado no risco.
        """
        return {
            "assessment": assessment.to_dict(),
            "mentoring_priority": {
                "focus_fields": [f.field for f in assessment.red_flags if f.field],
                "conversation_starters": [f.suggestion for f in assessment.red_flags if f.suggestion],
                "probing_questions": self._generate_probing_questions(assessment),
            }
        }
    
    def _generate_probing_questions(self, assessment: RiskAssessment) -> List[str]:
        """Gera perguntas de aprofundamento baseado no risco."""
        
        questions = []
        
        for flag in assessment.red_flags:
            if flag.flag_type == "generic_response":
                questions.append(
                    "Pode dar um exemplo concreto de [seu negócio]? Qual é um caso específico?"
                )
            elif flag.flag_type == "coherence_violation":
                questions.append(
                    "Como isso alinha com a decisão anterior que você tomou?"
                )
        
        return questions
