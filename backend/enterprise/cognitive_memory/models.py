"""
Cognitive Memory Layer
======================

Persistência de contexto estratégico entre templates e etapas.

Conecta decisões ao longo do tempo:
- Founder responde ICP em Q1 → Memoria registra
- Founder responde Persona em Q2 → Sistema detecta alinhamento/contradição
- Founder revisa Strategy em Q3 → Sistema avalia coerência retroativa

IMPORTANTE:
- Não usa embeddings (opcional)
- Apenas contexto explícito (JSON)
- Query por template, campo, período
- Usado apenas se ativado

Estrutura:
```
{
  "startup_id": "...",
  "template_key": "icp_01",
  "field_key": "company_size",
  "value": "small",
  "context": {
    "decision_date": "2025-01-08",
    "related_fields": {
      "industry": "SaaS",
      "budget": "10k-50k"
    },
    "implications": [
      "Focus on cost-sensitive buyers",
      "Need viral growth channel"
    ]
  },
  "inference": "Small company size + SaaS → Bootstrap mentality"
}
```
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, String, JSON, DateTime, Text, Index
from sqlalchemy.orm import Session
import uuid
import logging

from backend.db.database import Base

logger = logging.getLogger(__name__)


class StrategicMemory(Base):
    """
    Memória estratégica persistida.
    
    Cada registro é um snapshot de contexto em um momento específico.
    Imutável (append-only).
    """
    __tablename__ = "strategic_memory"
    
    id = Column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Identificação
    startup_id = Column(String(100), nullable=False, index=True)
    template_key = Column(String(255), nullable=False, index=True)
    field_key = Column(String(255), nullable=False)
    
    # O valor decidido
    value = Column(JSON, nullable=False)
    
    # Contexto rico
    context = Column(JSON, nullable=True)  # Dados relacionados naquele momento
    reasoning = Column(Text, nullable=True)  # Por quê foi decidido
    
    # Inferências automáticas
    implications = Column(JSON, nullable=True)  # Consequências esperadas
    inference = Column(Text, nullable=True)  # Síntese automática da decisão
    
    # Rastreamento
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ttl_days = Column(int, default=365)  # Quando expira da memória ativa
    
    __table_args__ = (
        Index('idx_memory_startup', 'startup_id'),
        Index('idx_memory_template', 'startup_id', 'template_key'),
        Index('idx_memory_created', 'created_at'),
    )


class CognitiveMemoryService:
    """Serviço de memória estratégica."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_memory(
        self,
        startup_id: str,
        template_key: str,
        field_key: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
        reasoning: Optional[str] = None,
        implications: Optional[List[str]] = None,
        inference: Optional[str] = None,
    ) -> Optional[StrategicMemory]:
        """
        Registra um evento estratégico na memória.
        
        Args:
            startup_id: ID da startup
            template_key: Ex: "icp_01"
            field_key: Ex: "company_size"
            value: Valor decidido
            context: Contexto rico (relacionados, metadata)
            reasoning: Justificativa
            implications: Consequências esperadas
            inference: Síntese automática
        
        Returns:
            StrategicMemory criado
        """
        try:
            memory = StrategicMemory(
                startup_id=startup_id,
                template_key=template_key,
                field_key=field_key,
                value=value,
                context=context,
                reasoning=reasoning,
                implications=implications,
                inference=inference,
            )
            
            self.db.add(memory)
            self.db.commit()
            
            logger.info(
                f"💭 Memória registrada: {startup_id} → {template_key}.{field_key}"
            )
            
            return memory
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar memória: {e}")
            self.db.rollback()
            return None
    
    def get_template_memory(
        self,
        startup_id: str,
        template_key: str,
        limit: int = 100,
    ) -> List[StrategicMemory]:
        """Retorna memória de um template."""
        
        return (
            self.db.query(StrategicMemory)
            .filter(
                StrategicMemory.startup_id == startup_id,
                StrategicMemory.template_key == template_key,
            )
            .order_by(StrategicMemory.created_at.desc())
            .limit(limit)
            .all()
        )
    
    def get_strategic_context(
        self,
        startup_id: str,
        templates: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retorna contexto estratégico completo.
        
        Útil para:
        - AI Mentor entender strategy geral
        - Detectar incoerências
        - Gerar recomendações
        """
        
        query = self.db.query(StrategicMemory).filter(
            StrategicMemory.startup_id == startup_id
        )
        
        if templates:
            query = query.filter(StrategicMemory.template_key.in_(templates))
        
        memories = query.order_by(StrategicMemory.created_at.desc()).limit(500).all()
        
        # Organiza por template
        context = {}
        for memory in memories:
            if memory.template_key not in context:
                context[memory.template_key] = []
            
            context[memory.template_key].append({
                "field": memory.field_key,
                "value": memory.value,
                "reasoning": memory.reasoning,
                "inference": memory.inference,
                "implications": memory.implications,
                "recorded_at": memory.created_at.isoformat(),
            })
        
        return context
    
    def find_related_decisions(
        self,
        startup_id: str,
        template_key: str,
        field_key: str,
    ) -> Dict[str, Any]:
        """
        Encontra decisões relacionadas por implicações.
        
        Ex: Se decidiu "Small ICP", que campos isso afeta?
        """
        
        memory = (
            self.db.query(StrategicMemory)
            .filter(
                StrategicMemory.startup_id == startup_id,
                StrategicMemory.template_key == template_key,
                StrategicMemory.field_key == field_key,
            )
            .order_by(StrategicMemory.created_at.desc())
            .first()
        )
        
        if not memory:
            return {}
        
        return {
            "decision": {
                "field": memory.field_key,
                "value": memory.value,
                "made_at": memory.created_at.isoformat(),
            },
            "implications": memory.implications or [],
            "reasoning": memory.reasoning,
            "related_fields": [
                # Busca campos relacionados nas implicações
                impl.split("→")[-1].strip() 
                for impl in (memory.implications or [])
                if "→" in impl
            ],
        }
