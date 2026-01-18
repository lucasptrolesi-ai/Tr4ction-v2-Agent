"""
Risk Signals (Phase 2)
----------------------

Append-only log of strategic risks detected for decisions/templates.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import logging

from sqlalchemy import Column, String, JSON, DateTime, Index
from sqlalchemy.orm import Session

from backend.db.database import Base

logger = logging.getLogger(__name__)


class RiskSignal(Base):
    """Persistent risk signal with evidence and dependencies."""

    __tablename__ = "risk_signals"
    __table_args__ = (
        Index("idx_risk_client", "client_id"),
        Index("idx_risk_template", "template_key"),
        Index("idx_risk_severity", "severity"),
        {"extend_existing": True},
    )

    id = Column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(100), nullable=False, index=True)
    template_key = Column(String(255), nullable=True, index=True)
    related_decisions = Column(JSON, nullable=True)
    risk_type = Column(String(100), nullable=False)  # incoherence | assumption_gap | market_mismatch
    severity = Column(String(20), nullable=False)  # LOW | MEDIUM | HIGH | CRITICAL
    evidence = Column(JSON, nullable=True)
    violated_dependencies = Column(JSON, nullable=True)
    recommendation = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "template_key": self.template_key,
            "related_decisions": self.related_decisions or [],
            "risk_type": self.risk_type,
            "severity": self.severity,
            "evidence": self.evidence or [],
            "violated_dependencies": self.violated_dependencies or [],
            "recommendation": self.recommendation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RiskSignalService:
    """Service to persist and fetch risk signals."""

    def __init__(self, db: Session):
        self.db = db

    def record_signal(
        self,
        client_id: str,
        template_key: Optional[str],
        risk_type: str,
        severity: str,
        evidence: Optional[List[Dict[str, Any]]],
        violated_dependencies: Optional[List[str]],
        recommendation: Optional[str],
        related_decisions: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[RiskSignal]:
        try:
            signal = RiskSignal(
                client_id=client_id,
                template_key=template_key,
                risk_type=risk_type,
                severity=severity,
                evidence=evidence or [],
                violated_dependencies=violated_dependencies or [],
                recommendation=recommendation,
                related_decisions=related_decisions or [],
            )
            self.db.add(signal)
            self.db.commit()
            return signal
        except Exception as exc:
            logger.error(f"Failed to record risk signal: {exc}")
            self.db.rollback()
            return None

    def list_signals(self, client_id: str, limit: int = 50) -> List[RiskSignal]:
        return (
            self.db.query(RiskSignal)
            .filter(RiskSignal.client_id == client_id)
            .order_by(RiskSignal.created_at.desc())
            .limit(limit)
            .all()
        )
