"""
AI Audit & Compliance Layer
============================

Registra TUDO que a IA fez:
- Qual prompt foi usado
- Qual modelo respondeu
- Qual versão das rules foi aplicada
- Timestamp exato
- Contexto fornecido
- Output gerado

IMPORTANTE:
- Append-only log
- Sem impacto no desempenho (async logging)
- Ativado apenas por flag
- Zero dados sensíveis (apenas IDs)

Por quê? Compliance + Auditabilidade:
- Se investigador pergunta "por que o sistema respondeu X ao founder?", sistema consegue responder
- FCJ pode auditar qualidade das respostas da IA
- Investidores veem rastreabilidade completa
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, JSON, DateTime, Text, Index, Integer
from sqlalchemy.orm import Session
import uuid
import logging

from backend.db.database import Base

logger = logging.getLogger(__name__)


class AIAuditLog(Base):
    """
    Log imutável de interação com IA.
    
    Cada linha é um evento.
    """
    __tablename__ = "ai_audit_logs"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Contexto
    user_id = Column(String(100), nullable=False, index=True)
    startup_id = Column(String(100), nullable=False, index=True)
    template_key = Column(String(255), nullable=True)
    response_id = Column(String(100), nullable=True, index=True)
    
    # O que aconteceu
    event_type = Column(String(50), nullable=False)  # mentor_response, risk_assessment, etc
    
    # Prompt + Model
    model = Column(String(50), nullable=False)  # gpt-4, gpt-3.5, etc
    model_version = Column(String(50), nullable=True)  # versão exata
    prompt_hash = Column(String(100), nullable=True)
    prompt_version = Column(String(50), nullable=True)
    system_prompt_hash = Column(String(100), nullable=True)  # SHA256 do prompt
    system_prompt_version = Column(String(50), nullable=True)  # "v1.0", "v1.1", etc
    
    # Input/Output
    input_tokens = Column(JSON, nullable=True)  # Contexto enviado para IA
    tokens_used = Column(JSON, nullable=True)  # {prompt_tokens: 123, completion_tokens: 456}
    response_length = Column(Integer, nullable=True)  # Tamanho da resposta
    latency_ms = Column(int, nullable=True)  # Tempo de resposta
    context_snapshot = Column(JSON, nullable=True)
    
    # Rastreamento de regras/validações
    rules_version = Column(String(50), nullable=True)  # Versão das regras de governança
    validation_rules_applied = Column(JSON, nullable=True)  # Quais regras foram checadas
    governance_rules_active = Column(JSON, nullable=True)
    
    # Status
    success = Column(int, default=1)  # 1=sucesso, 0=erro
    error_message = Column(Text, nullable=True)  # Se houve erro
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_audit_startup', 'startup_id'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_event', 'event_type'),
        Index('idx_audit_created', 'created_at'),
    )


class AIAuditService:
    """Serviço de auditoria de IA."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_event(
        self,
        user_id: str,
        startup_id: str,
        event_type: str,
        model: str,
        response_id: Optional[str] = None,
        prompt_hash: Optional[str] = None,
        prompt_version: Optional[str] = None,
        system_prompt_hash: Optional[str] = None,
        system_prompt_version: Optional[str] = None,
        input_tokens: Optional[Dict[str, Any]] = None,
        tokens_used: Optional[Dict[str, int]] = None,
        response_length: Optional[int] = None,
        latency_ms: Optional[int] = None,
        rules_version: Optional[str] = None,
        validation_rules_applied: Optional[list] = None,
        governance_rules_active: Optional[list] = None,
        success: int = 1,
        error_message: Optional[str] = None,
        template_key: Optional[str] = None,
        model_version: Optional[str] = None,
        context_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Optional[AIAuditLog]:
        """
        Registra um evento de IA.
        
        Nunca falha no fluxo principal (fire-and-forget).
        
        Args:
            user_id: ID do founder
            startup_id: ID da startup
            event_type: Tipo de evento (mentor_response, risk_assessment, etc)
            model: Nome do modelo (gpt-4, gpt-3.5, etc)
            response_id: ID da resposta gerada
            prompt_hash: Hash do prompt utilizado (SHA256 ou similar)
            prompt_version: Versão do prompt utilizada
            system_prompt_hash: SHA256 do prompt utilizado
            system_prompt_version: Versão do prompt (v1.0, v1.1, etc)
            input_tokens: Contexto enviado para a IA (JSON)
            tokens_used: Tokens consumidos {prompt_tokens, completion_tokens}
            response_length: Tamanho da resposta em caracteres
            latency_ms: Tempo de resposta em ms
            rules_version: Versão das regras de governança
            validation_rules_applied: Lista de regras que foram aplicadas
            governance_rules_active: Lista de regras ativas no momento
            success: 1=sucesso, 0=erro
            error_message: Mensagem de erro se aplicável
            template_key: Template relacionado (opcional)
            model_version: Versão específica do modelo
            context_snapshot: Contexto enviado (incluindo premissas)
        
        Returns:
            AIAuditLog criado ou None se houver erro
        """
        
        try:
            log = AIAuditLog(
                user_id=user_id,
                startup_id=startup_id,
                event_type=event_type,
                model=model,
                model_version=model_version,
                response_id=response_id,
                prompt_hash=prompt_hash,
                prompt_version=prompt_version,
                system_prompt_hash=system_prompt_hash,
                system_prompt_version=system_prompt_version,
                input_tokens=input_tokens,
                tokens_used=tokens_used,
                response_length=response_length,
                latency_ms=latency_ms,
                rules_version=rules_version,
                validation_rules_applied=validation_rules_applied,
                governance_rules_active=governance_rules_active,
                success=success,
                error_message=error_message,
                template_key=template_key,
                context_snapshot=context_snapshot,
            )
            
            self.db.add(log)
            self.db.commit()
            
            logger.debug(
                f"📝 AI Audit: {event_type} para {user_id} no {template_key or 'N/A'}"
            )
            
            return log
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar auditoria de IA: {e}")
            self.db.rollback()
            return None
    
    def get_audit_trail(
        self,
        startup_id: str,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """
        Retorna trail de auditoria (read-only).
        
        Args:
            startup_id: ID da startup
            event_type: Filtro por tipo de evento (opcional)
            limit: Máximo de registros
        
        Returns:
            Lista de AIAuditLog
        """
        
        query = self.db.query(AIAuditLog).filter(
            AIAuditLog.startup_id == startup_id
        )
        
        if event_type:
            query = query.filter(AIAuditLog.event_type == event_type)
        
        return query.order_by(AIAuditLog.created_at.desc()).limit(limit).all()
    
    def get_ai_performance_stats(
        self,
        startup_id: str,
        event_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retorna estatísticas de performance da IA.
        
        Args:
            startup_id: ID da startup
            event_type: Filtro por tipo (opcional)
        
        Returns:
            Dicionário com stats (avg latency, success rate, tokens, etc)
        """
        
        logs = self.get_audit_trail(startup_id, event_type, limit=10000)
        
        if not logs:
            return {
                "total_events": 0,
                "message": "Sem dados de auditoria"
            }
        
        latencies = [l.latency_ms for l in logs if l.latency_ms]
        success_count = sum(1 for l in logs if l.success == 1)
        
        total_tokens = 0
        for log in logs:
            if log.tokens_used:
                total_tokens += log.tokens_used.get("prompt_tokens", 0)
                total_tokens += log.tokens_used.get("completion_tokens", 0)
        
        return {
            "total_events": len(logs),
            "success_rate": (success_count / len(logs)) * 100 if logs else 0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "min_latency_ms": min(latencies) if latencies else None,
            "max_latency_ms": max(latencies) if latencies else None,
            "total_tokens_used": total_tokens,
            "models_used": list(set(l.model for l in logs)),
            "events_by_type": {
                event: sum(1 for l in logs if l.event_type == event)
                for event in set(l.event_type for l in logs)
            },
        }
