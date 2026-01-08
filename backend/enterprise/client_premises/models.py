"""
Client Premises & Context Foundation (Phase 1)
----------------------------------------------

Append-only, versioned premises per client. Only one active version per client.
- Never delete rows
- New versions append, previous active marked as superseded
- Designed for safe observation (no blocking in Phase 1)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
import uuid

from sqlalchemy import Column, String, Integer, JSON, DateTime, Index
from sqlalchemy.orm import Session

from backend.db.database import Base
from backend.enterprise.config import get_or_create_enterprise_config

logger = logging.getLogger(__name__)


class ClientPremise(Base):
    """Premissas estratégicas versionadas por cliente."""

    __tablename__ = "client_premises"

    id = Column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(100), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    assumptions = Column(JSON, nullable=False)
    constraints = Column(JSON, nullable=True)
    objectives = Column(JSON, nullable=True)
    status = Column(String(50), default="active")  # active | superseded
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_premises_client_version", "client_id", "version"),
        Index("idx_premises_client_status", "client_id", "status"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "version": self.version,
            "assumptions": self.assumptions or [],
            "constraints": self.constraints or [],
            "objectives": self.objectives or [],
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ClientPremiseService:
    """Serviço para leitura/registro de premissas versionadas (append-only)."""

    def __init__(self, db: Session):
        self.db = db
        self.config = get_or_create_enterprise_config()

    def _next_version(self, client_id: str) -> int:
        last = (
            self.db.query(ClientPremise)
            .filter(ClientPremise.client_id == client_id)
            .order_by(ClientPremise.version.desc())
            .first()
        )
        return (last.version + 1) if last else 1

    def get_active_premise(self, client_id: str) -> Optional[ClientPremise]:
        return (
            self.db.query(ClientPremise)
            .filter(ClientPremise.client_id == client_id, ClientPremise.status == "active")
            .order_by(ClientPremise.version.desc())
            .first()
        )

    def list_premises(self, client_id: str, limit: int = 20) -> List[ClientPremise]:
        return (
            self.db.query(ClientPremise)
            .filter(ClientPremise.client_id == client_id)
            .order_by(ClientPremise.version.desc())
            .limit(limit)
            .all()
        )

    def create_premise(
        self,
        client_id: str,
        assumptions: List[str],
        constraints: Optional[List[str]] = None,
        objectives: Optional[List[str]] = None,
        status: str = "active",
    ) -> Optional[ClientPremise]:
        """Cria nova versão de premissas. Marca anterior como superseded se necessário."""

        try:
            next_version = self._next_version(client_id)

            if status == "active":
                previous_active = self.get_active_premise(client_id)
                if previous_active:
                    previous_active.status = "superseded"

            premise = ClientPremise(
                client_id=client_id,
                version=next_version,
                assumptions=assumptions or [],
                constraints=constraints or [],
                objectives=objectives or [],
                status=status,
            )

            self.db.add(premise)
            self.db.commit()
            return premise
        except Exception as exc:
            logger.error(f"Failed to create client premise: {exc}")
            self.db.rollback()
            return None

    def ensure_premise_or_fallback(self, client_id: str) -> Dict[str, Any]:
        """Retorna premissa ativa ou fallback seguro para não bloquear respostas."""

        active = self.get_active_premise(client_id)
        if active:
            return {"premises": active.to_dict(), "status": "active"}

        fallback = {
            "premises": {
                "client_id": client_id,
                "assumptions": [],
                "constraints": [],
                "objectives": [],
                "status": "fallback",
                "created_at": datetime.utcnow().isoformat(),
            },
            "status": "fallback",
        }
        return fallback

