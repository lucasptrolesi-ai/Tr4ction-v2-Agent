"""
Method Governance Engine
========================

Enforça regras do método FCJ:
- Gates por etapa
- Validações mínimas obrigatórias
- Checkpoints de coerência
- Capacidade de bloquear avanço (somente se flag ativa)

IMPORTANTE:
- É um OBSERVER puro - nunca altera o fluxo se desligado
- Se ativo, retorna warnings + pode bloquear
- Rules são declarativas (YAML/JSON)
- Compatível com múltiplas versões do método

Fluxo:
1. Founder tenta salvar template
2. Governance verifica ANTES de persistir
3. Retorna lista de violations
4. Se crítico + flag BLOCK_ON_CRITICAL = True, rejeita
5. Se não, salva com warnings (sugestões)
"""

from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import yaml
import json
import logging
from pathlib import Path

from backend.enterprise.governance.models import GovernanceGate

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Níveis de risco de uma violação."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """Uma regra de validação do método FCJ."""
    
    field: str  # Ex: "icp.company_size"
    rule_type: Literal["required", "pattern", "range", "coherence", "custom"]
    message: str
    risk_level: RiskLevel = RiskLevel.MEDIUM
    applies_to_templates: List[str] = field(default_factory=list)
    enabled: bool = True
    
    # Configurações específicas por tipo
    pattern: Optional[str] = None  # Para type=pattern
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: Optional[List[str]] = None
    required_fields: Optional[List[str]] = None  # Campos obrigatórios
    coherence_check: Optional[str] = None  # Campo relacionado para validar


@dataclass
class GovernanceViolation:
    """Uma violação detectada."""
    
    field: str
    rule_type: str
    message: str
    risk_level: RiskLevel
    template_key: str
    current_value: Any
    expected_pattern: Optional[str] = None
    suggestion: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para API."""
        return {
            "field": self.field,
            "rule_type": self.rule_type,
            "message": self.message,
            "risk_level": self.risk_level.value,
            "template_key": self.template_key,
            "current_value": self.current_value,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class GovernanceGateResult:
    """Resultado da avaliação de um gate declarativo."""

    gate_id: str
    gate_version: int
    template_id: str
    vertical: Optional[str]
    passed: bool
    violations: List[GovernanceViolation] = field(default_factory=list)
    min_completeness_score: Optional[int] = None
    completeness_score: Optional[float] = None
    block_on_fail: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_version": self.gate_version,
            "template_id": self.template_id,
            "vertical": self.vertical,
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
            "min_completeness_score": self.min_completeness_score,
            "completeness_score": self.completeness_score,
            "block_on_fail": self.block_on_fail,
            "timestamp": self.timestamp.isoformat(),
        }


class GovernanceEngine:
    """Motor de validação de governança do método FCJ."""
    
    # Rules default (podem ser override)
    DEFAULT_RULES = [
        # ICP validations
        ValidationRule(
            field="icp.company_size",
            rule_type="required",
            message="Tamanho da empresa é obrigatório no ICP",
            risk_level=RiskLevel.HIGH,
            applies_to_templates=["icp_01"],
        ),
        ValidationRule(
            field="icp.industry",
            rule_type="required",
            message="Indústria é obrigatória no ICP",
            risk_level=RiskLevel.HIGH,
            applies_to_templates=["icp_01"],
        ),
        
        # Persona validations
        ValidationRule(
            field="persona.pain_points",
            rule_type="required",
            message="Pain points são obrigatórios na Persona",
            risk_level=RiskLevel.HIGH,
            applies_to_templates=["persona_01"],
            min_length=50,
        ),
        ValidationRule(
            field="persona.goals",
            rule_type="required",
            message="Goals são obrigatórios na Persona",
            risk_level=RiskLevel.HIGH,
            applies_to_templates=["persona_01"],
            min_length=30,
        ),
        
        # General
        ValidationRule(
            field="*",
            rule_type="pattern",
            message="Resposta genérica demais (palavras-chave: 'aumentar', 'melhorar' sem contexto)",
            risk_level=RiskLevel.MEDIUM,
            pattern=r"^(aumentar|melhorar|good|better)$",
        ),
    ]
    
    def __init__(self, custom_rules: Optional[List[ValidationRule]] = None):
        """
        Inicializa engine.
        
        Args:
            custom_rules: Lista de regras customizadas (override do default)
        """
        self.rules = custom_rules or self.DEFAULT_RULES
        logger.info(f"✓ Governance engine carregado com {len(self.rules)} regras")
    
    def validate_template_data(
        self,
        template_key: str,
        data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]] = None,
    ) -> List[GovernanceViolation]:
        """
        Valida dados de um template contra as regras.
        
        Args:
            template_key: Ex: "persona_01"
            data: Dados a validar
            previous_data: Dados anteriores (para detecção de mudanças)
        
        Returns:
            Lista de violações encontradas (vazia se OK)
        """
        violations = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Verifica se regra se aplica a este template
            if rule.applies_to_templates and template_key not in rule.applies_to_templates:
                continue
            
            # Executa validação
            if rule.rule_type == "required":
                violation = self._check_required(rule, template_key, data)
                if violation:
                    violations.append(violation)
            
            elif rule.rule_type == "pattern":
                for field_key, value in data.items():
                    violation = self._check_pattern(rule, template_key, field_key, value)
                    if violation:
                        violations.append(violation)
            
            elif rule.rule_type == "coherence":
                violation = self._check_coherence(rule, template_key, data, previous_data)
                if violation:
                    violations.append(violation)
        
        return violations

    def evaluate_gate(
        self,
        gate: GovernanceGate,
        template_key: str,
        data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]] = None,
    ) -> GovernanceGateResult:
        """Avalia um gate declarativo contra dados atuais."""

        violations: List[GovernanceViolation] = []

        # required_fields
        for field_name in gate.required_fields or []:
            value = data.get(field_name)
            if value in (None, "") or (isinstance(value, list) and len(value) == 0):
                violations.append(
                    GovernanceViolation(
                        field=field_name,
                        rule_type="required",
                        message=f"Campo obrigatório ausente: {field_name}",
                        risk_level=RiskLevel.HIGH,
                        template_key=template_key,
                        current_value=value,
                        suggestion=f"Preencha '{field_name}' para avançar.",
                    )
                )

        # validation_rules (lightweight checks)
        for rule in gate.validation_rules or []:
            rule_field = rule.get("field")
            rule_type = rule.get("type")
            message = rule.get("message", "Regra de governança não atendida")
            risk_level = RiskLevel(rule.get("risk_level", "medium"))
            value = data.get(rule_field) if rule_field else None

            if rule_type == "min_length" and isinstance(value, str):
                min_len = int(rule.get("min_length", 0))
                if len(value) < min_len:
                    violations.append(
                        GovernanceViolation(
                            field=rule_field or "*",
                            rule_type="min_length",
                            message=message,
                            risk_level=risk_level,
                            template_key=template_key,
                            current_value=value,
                            suggestion=f"Forneça pelo menos {min_len} caracteres",
                        )
                    )

            if rule_type == "pattern" and isinstance(value, str) and rule.get("pattern"):
                import re

                if re.match(rule["pattern"], value, re.IGNORECASE):
                    violations.append(
                        GovernanceViolation(
                            field=rule_field or "*",
                            rule_type="pattern",
                            message=message,
                            risk_level=risk_level,
                            template_key=template_key,
                            current_value=value,
                            suggestion=rule.get("suggestion"),
                        )
                    )

        completeness_score = self._compute_completeness_score(data)
        passed = len(violations) == 0 and (
            gate.min_completeness_score is None
            or completeness_score >= (gate.min_completeness_score or 0)
        )

        return GovernanceGateResult(
            gate_id=gate.id,
            gate_version=gate.version,
            template_id=gate.template_id,
            vertical=gate.vertical,
            passed=passed,
            violations=violations,
            min_completeness_score=gate.min_completeness_score,
            completeness_score=completeness_score,
            block_on_fail=bool(gate.block_on_fail),
        )

    @staticmethod
    def _compute_completeness_score(data: Dict[str, Any]) -> float:
        if not data:
            return 0.0
        filled = sum(1 for v in data.values() if v not in (None, "", [], {}))
        total = len(data)
        return round((filled / total) * 100, 2) if total > 0 else 0.0
    
    def _check_required(
        self,
        rule: ValidationRule,
        template_key: str,
        data: Dict[str, Any],
    ) -> Optional[GovernanceViolation]:
        """Verifica se campo obrigatório está preenchido."""
        
        field_key = rule.field.split(".")[-1]  # "icp.company_size" → "company_size"
        
        value = data.get(field_key)
        
        # Campos vazios
        if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
            return GovernanceViolation(
                field=field_key,
                rule_type="required",
                message=rule.message,
                risk_level=rule.risk_level,
                template_key=template_key,
                current_value=value,
                suggestion=f"Preencha o campo '{field_key}' antes de avançar",
            )
        
        # Tamanho mínimo
        if rule.min_length and isinstance(value, str) and len(value) < rule.min_length:
            return GovernanceViolation(
                field=field_key,
                rule_type="required",
                message=rule.message,
                risk_level=RiskLevel.MEDIUM,
                template_key=template_key,
                current_value=value,
                suggestion=f"Resposta muito breve. Mínimo {rule.min_length} caracteres.",
            )
        
        return None
    
    def _check_pattern(
        self,
        rule: ValidationRule,
        template_key: str,
        field_key: str,
        value: Any,
    ) -> Optional[GovernanceViolation]:
        """Verifica se valor segue padrão."""
        
        if not rule.pattern or not isinstance(value, str):
            return None
        
        import re
        if re.match(rule.pattern, value, re.IGNORECASE):
            return GovernanceViolation(
                field=field_key,
                rule_type="pattern",
                message=rule.message,
                risk_level=rule.risk_level,
                template_key=template_key,
                current_value=value,
                suggestion="Sua resposta é muito genérica. Seja mais específico.",
                expected_pattern=rule.pattern,
            )
        
        return None
    
    def _check_coherence(
        self,
        rule: ValidationRule,
        template_key: str,
        data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[GovernanceViolation]:
        """Verifica coerência com dados anteriores."""
        
        # Placeholder para validações customizadas
        return None
    
    def load_rules_from_yaml(self, yaml_path: str):
        """Carrega regras de um arquivo YAML."""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                rules_data = yaml.safe_load(f)
            
            self.rules = [
                ValidationRule(
                    field=r["field"],
                    rule_type=r["rule_type"],
                    message=r["message"],
                    risk_level=RiskLevel(r.get("risk_level", "medium")),
                    applies_to_templates=r.get("applies_to_templates", []),
                    pattern=r.get("pattern"),
                    min_length=r.get("min_length"),
                    max_length=r.get("max_length"),
                )
                for r in rules_data.get("rules", [])
            ]
            
            logger.info(f"✓ Carregadas {len(self.rules)} regras de {yaml_path}")
        
        except Exception as e:
            logger.error(f"❌ Erro ao carregar rules YAML: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do engine."""
        by_level = {}
        for rule in self.rules:
            level = rule.risk_level.value
            by_level[level] = by_level.get(level, 0) + 1
        
        return {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules if r.enabled),
            "by_risk_level": by_level,
        }
