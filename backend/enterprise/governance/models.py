"""
Governance Gates (Phase 2)
-------------------------

Declarative, append-only gates for method governance.
Stored in DB to allow versioning and per-vertical customization.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import logging

from sqlalchemy import Column, String, Integer, JSON, DateTime, Boolean, Index
from sqlalchemy.orm import Session

from backend.db.database import Base

logger = logging.getLogger(__name__)


class GovernanceGate(Base):
    """Append-only governance gate definition."""

    __tablename__ = "governance_gates"
    __table_args__ = (
        Index("idx_gate_template_vertical", "template_id", "vertical"),
        Index("idx_gate_template_version", "template_id", "version"),
        {"extend_existing": True},
    )

    id = Column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(255), nullable=False, index=True)
    vertical = Column(String(100), nullable=True, index=True)
    required_fields = Column(JSON, nullable=True)  # list[str]
    validation_rules = Column(JSON, nullable=True)  # list of rule dicts
    min_completeness_score = Column(Integer, nullable=True, default=0)
    block_on_fail = Column(Boolean, default=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "template_id": self.template_id,
            "vertical": self.vertical,
            "required_fields": self.required_fields or [],
            "validation_rules": self.validation_rules or [],
            "min_completeness_score": self.min_completeness_score,
            "block_on_fail": bool(self.block_on_fail),
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GovernanceGateService:
    """Service for loading gates and registering new versions (append-only)."""

    def __init__(self, db: Session):
        self.db = db

    def list_gates(self, template_id: str, vertical: Optional[str] = None) -> List[GovernanceGate]:
        query = (
            self.db.query(GovernanceGate)
            .filter(GovernanceGate.template_id == template_id)
            .order_by(GovernanceGate.version.desc(), GovernanceGate.created_at.desc())
        )
        if vertical:
            query = query.filter((GovernanceGate.vertical == vertical) | (GovernanceGate.vertical.is_(None)))
        return query.all()

    def latest_gate(self, template_id: str, vertical: Optional[str] = None) -> Optional[GovernanceGate]:
        gates = self.list_gates(template_id, vertical)
        return gates[0] if gates else None

    def create_gate(
        self,
        template_id: str,
        vertical: Optional[str],
        required_fields: Optional[List[str]],
        validation_rules: Optional[List[Dict[str, Any]]],
        min_completeness_score: Optional[int],
        block_on_fail: bool,
        version: int,
    ) -> Optional[GovernanceGate]:
        try:
            gate = GovernanceGate(
                template_id=template_id,
                vertical=vertical,
                required_fields=required_fields or [],
                validation_rules=validation_rules or [],
                min_completeness_score=min_completeness_score,
                block_on_fail=block_on_fail,
                version=version,
            )
            self.db.add(gate)
            self.db.commit()
            return gate
        except Exception as exc:
            logger.error(f"Failed to create governance gate: {exc}")
            self.db.rollback()
            return None
