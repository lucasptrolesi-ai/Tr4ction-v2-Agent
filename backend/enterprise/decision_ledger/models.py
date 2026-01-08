"""
Decision Ledger - Event Sourcing Leve
======================================

Registra TODAS as decisões tomadas pelos founders com:
- O QUÊ: Campo, valor, tipo
- QUANDO: Timestamp exato
- QUEM: User ID, email
- ONDE: Template, etapa, field
- POR QUÊ: Contexto, premissas
- MÉTODO: Versão do FCJ usado
- STATUS: Esperado vs. Real (após 30 dias)

IMPORTANTE:
- É um append-only log (imutável)
- Sem dependência com StepAnswer
- Rastreável e auditável
- Apenas leitura para API
- Nunca bloqueia o fluxo
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, String, Integer, JSON, DateTime, Text, Index
from sqlalchemy.orm import Session
import uuid
import logging

from backend.db.database import Base
from backend.enterprise.config import get_or_create_enterprise_config

logger = logging.getLogger(__name__)


class DecisionEvent(Base):
    """
    Modelo de evento de decisão (imutável).
    
    Cada linha é UMA decisão tomada por UM founder em UM momento específico.
    Nunca é atualizada, apenas inserida.
    """
    __tablename__ = "decision_events"
    
    # Identificação
    id = Column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Quem decidiu
    user_id = Column(String(100), nullable=False, index=True)
    user_email = Column(String(255), nullable=False)
    
    # Contexto da decisão
    startup_id = Column(String(100), nullable=False, index=True)
    template_key = Column(String(255), nullable=False, index=True)
    field_key = Column(String(255), nullable=False)
    step_id = Column(String(100), nullable=True)
    
    # A decisão em si
    field_label = Column(String(255), nullable=True)  # Ex: "ICP Company Size"
    previous_value = Column(JSON, nullable=True)  # Valor anterior (se houve)
    new_value = Column(JSON, nullable=False)  # Novo valor decidido
    value_type = Column(String(50), nullable=False)  # text, number, json, list
    
    # Contexto metodológico
    fcj_method_version = Column(String(50), default="v1.0")  # Versão do método
    cycle = Column(String(50), nullable=True)  # Q1, Q2, etc.
    
    # Premissas e justificativa
    reasoning = Column(Text, nullable=True)  # Por quê foi decidido
    source = Column(String(50), default="founder")  # founder, ai_mentor, import, admin
    
    # Contexto relacionado (snapshot)
    related_template_snapshot = Column(JSON, nullable=True)  # Dados de templates relacionados
    
    # Timestamp (imutável)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Consequências esperadas vs reais (preenchido depois)
    expected_outcome = Column(Text, nullable=True)
    actual_outcome = Column(Text, nullable=True)
    outcome_verified_at = Column(DateTime, nullable=True)
    outcome_success = Column(Integer, nullable=True)  # -1=falhou, 0=incerto, 1=sucesso
    
    __table_args__ = (
        Index('idx_decision_startup_template', 'startup_id', 'template_key'),
        Index('idx_decision_user_timestamp', 'user_id', 'created_at'),
        Index('idx_decision_created_at', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa evento para API."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "startup_id": self.startup_id,
            "template_key": self.template_key,
            "field_key": self.field_key,
            "field_label": self.field_label,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "value_type": self.value_type,
            "reasoning": self.reasoning,
            "source": self.source,
            "fcj_method_version": self.fcj_method_version,
            "cycle": self.cycle,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expected_outcome": self.expected_outcome,
            "actual_outcome": self.actual_outcome,
            "outcome_success": self.outcome_success,
        }


class DecisionLedgerService:
    """Serviço de persistência e query de decisões."""
    
    def __init__(self, db: Session):
        self.db = db
        self.config = get_or_create_enterprise_config()
    
    def record_decision(
        self,
        user_id: str,
        user_email: str,
        startup_id: str,
        template_key: str,
        field_key: str,
        new_value: Any,
        previous_value: Optional[Any] = None,
        field_label: Optional[str] = None,
        reasoning: Optional[str] = None,
        source: str = "founder",
        step_id: Optional[str] = None,
        fcj_method_version: str = "v1.0",
        cycle: Optional[str] = None,
        related_template_snapshot: Optional[Dict] = None,
    ) -> Optional[DecisionEvent]:
        """
        Registra uma decisão no ledger.
        
        Chamado APÓS qualquer mudança de valor importante.
        Nunca falha no fluxo - é fire-and-forget.
        
        Args:
            user_id: ID do founder
            user_email: Email do founder
            startup_id: ID da startup
            template_key: Ex: "persona_01"
            field_key: Ex: "pain_points"
            new_value: Valor decidido
            previous_value: Valor anterior (se aplicável)
            field_label: Nome legível do campo
            reasoning: Justificativa (opcional)
            source: Quem/como a decisão foi tomada
            step_id: Etapa relacionada
            fcj_method_version: Versão do FCJ
            cycle: Ciclo (Q1, Q2, etc)
            related_template_snapshot: Dados de templates relacionados
        
        Returns:
            DecisionEvent criado ou None se feature desligado
        """
        
        # 1. Verifica se feature está ativo
        if not self.config.decision_ledger:
            return None
        
        try:
            # 2. Cria evento
            event = DecisionEvent(
                user_id=user_id,
                user_email=user_email,
                startup_id=startup_id,
                template_key=template_key,
                field_key=field_key,
                new_value=new_value,
                previous_value=previous_value,
                field_label=field_label,
                value_type=type(new_value).__name__,
                reasoning=reasoning,
                source=source,
                step_id=step_id,
                fcj_method_version=fcj_method_version,
                cycle=cycle,
                related_template_snapshot=related_template_snapshot,
            )
            
            # 3. Persiste (append-only)
            self.db.add(event)
            self.db.commit()
            
            logger.info(
                f"📝 Decisão registrada: {user_email} → {template_key}.{field_key} = {new_value}"
            )
            
            return event
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar decisão: {e}")
            self.db.rollback()
            return None
    
    def get_decision_history(
        self,
        startup_id: str,
        template_key: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[DecisionEvent]:
        """
        Retorna histórico de decisões (read-only).
        
        Args:
            startup_id: ID da startup
            template_key: Filtro por template (opcional)
            user_id: Filtro por user (opcional)
            limit: Máximo de registros
        
        Returns:
            Lista de DecisionEvents (mais recentes primeiro)
        """
        
        if not self.config.decision_ledger:
            return []
        
        query = self.db.query(DecisionEvent).filter(
            DecisionEvent.startup_id == startup_id
        )
        
        if template_key:
            query = query.filter(DecisionEvent.template_key == template_key)
        
        if user_id:
            query = query.filter(DecisionEvent.user_id == user_id)
        
        return query.order_by(DecisionEvent.created_at.desc()).limit(limit).all()
    
    def get_decision_by_field(
        self,
        startup_id: str,
        template_key: str,
        field_key: str,
    ) -> List[DecisionEvent]:
        """Retorna todas as mudanças em um campo específico."""
        
        if not self.config.decision_ledger:
            return []
        
        return (
            self.db.query(DecisionEvent)
            .filter(
                DecisionEvent.startup_id == startup_id,
                DecisionEvent.template_key == template_key,
                DecisionEvent.field_key == field_key,
            )
            .order_by(DecisionEvent.created_at.desc())
            .all()
        )
    
    def update_outcome(
        self,
        event_id: str,
        expected_outcome: str,
        actual_outcome: Optional[str] = None,
        success: Optional[int] = None,
    ) -> Optional[DecisionEvent]:
        """
        Atualiza consequências esperadas vs reais.
        
        Chamado depois de 30 dias para validar se decisão teve impacto.
        """
        
        if not self.config.decision_ledger:
            return None
        
        event = self.db.query(DecisionEvent).filter(DecisionEvent.id == event_id).first()
        if not event:
            return None
        
        event.expected_outcome = expected_outcome
        event.actual_outcome = actual_outcome
        event.outcome_verified_at = datetime.utcnow()
        event.outcome_success = success
        
        self.db.commit()
        logger.info(f"✅ Consequência de decisão {event_id} atualizada")
        
        return event
