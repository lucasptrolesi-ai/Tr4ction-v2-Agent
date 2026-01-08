"""
Context Builder - Phase 4 Enhanced
===================================

Builds execution context with partner/vertical awareness.
Integrates with existing Template Registry, Governance, and Risk engines.

Fail-safe: Works perfectly without partner/vertical context.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import logging

from backend.enterprise.multi_vertical import (
    PartnerService,
    VerticalService,
    MethodProfileService,
)
from backend.enterprise.client_premises import ClientPremiseService
from backend.enterprise.config import get_or_create_enterprise_config

logger = logging.getLogger(__name__)


class ExecutionContext:
    """
    Execution context for template processing.
    
    Contains all metadata needed for:
    - Template selection
    - Governance evaluation
    - Risk assessment
    - Language tone formatting
    """
    
    def __init__(
        self,
        *,
        startup_id: str,
        user_id: str,
        template_key: str,
        partner_id: Optional[str] = None,
        vertical_id: Optional[str] = None,
        method_version: Optional[str] = None,
        language_tone: str = "consultative",
        premises: Optional[Dict[str, Any]] = None,
        governance_gate_refs: Optional[List[str]] = None,
        risk_rule_refs: Optional[List[str]] = None,
    ):
        self.startup_id = startup_id
        self.user_id = user_id
        self.template_key = template_key
        self.partner_id = partner_id or "fcj"
        self.vertical_id = vertical_id
        self.method_version = method_version or "v1.0"
        self.language_tone = language_tone
        self.premises = premises
        self.governance_gate_refs = governance_gate_refs or []
        self.risk_rule_refs = risk_rule_refs or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/audit."""
        return {
            "startup_id": self.startup_id,
            "user_id": self.user_id,
            "template_key": self.template_key,
            "partner_id": self.partner_id,
            "vertical_id": self.vertical_id,
            "method_version": self.method_version,
            "language_tone": self.language_tone,
            "has_premises": bool(self.premises),
            "governance_gates_count": len(self.governance_gate_refs),
            "risk_rules_count": len(self.risk_rule_refs),
        }


class ContextBuilder:
    """
    Builds execution context with partner/vertical awareness.
    
    Integrates:
    - Partner & Vertical metadata
    - Method profiles
    - Client premises
    - Feature flags
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.config = get_or_create_enterprise_config()
        self.partner_service = PartnerService(db)
        self.vertical_service = VerticalService(db)
        self.profile_service = MethodProfileService(db)
        self.premise_service = ClientPremiseService(db)
    
    def build(
        self,
        *,
        startup_id: str,
        user_id: str,
        template_key: str,
        partner_id: Optional[str] = None,
        vertical_id: Optional[str] = None,
        method_version: Optional[str] = None,
    ) -> ExecutionContext:
        """
        Build execution context.
        
        Fail-safe: If multi_vertical flag is OFF, uses FCJ defaults.
        """
        
        # Check if multi-vertical is enabled
        if not self.config.multi_vertical:
            logger.debug("Multi-vertical disabled, using FCJ defaults")
            return self._build_default_context(
                startup_id=startup_id,
                user_id=user_id,
                template_key=template_key
            )
        
        # Load partner
        partner = self.partner_service.get_or_default(partner_id)
        
        # Load vertical (optional)
        vertical = None
        if vertical_id:
            vertical = self.vertical_service.get_vertical(vertical_id)
            if not vertical:
                logger.warning(f"Vertical {vertical_id} not found, using partner defaults")
        
        # Load or create method profile
        profile = self.profile_service.get_or_create_default(
            partner_id=partner.id,
            vertical_id=vertical.id if vertical else None
        )
        
        # Compute effective language tone
        effective_tone = self.profile_service.compute_effective_tone(partner, vertical)
        
        # Load client premises
        premises_result = self.premise_service.ensure_premise_or_fallback(startup_id)
        premises = premises_result.get("premises") if premises_result else None
        
        # Build context
        context = ExecutionContext(
            startup_id=startup_id,
            user_id=user_id,
            template_key=template_key,
            partner_id=partner.id,
            vertical_id=vertical.id if vertical else None,
            method_version=profile.method_version,
            language_tone=effective_tone,
            premises=premises,
            governance_gate_refs=profile.governance_gate_refs or [],
            risk_rule_refs=profile.risk_rule_refs or [],
        )
        
        logger.info(f"Built context: {context.to_dict()}")
        return context
    
    def _build_default_context(
        self,
        *,
        startup_id: str,
        user_id: str,
        template_key: str,
    ) -> ExecutionContext:
        """Build default FCJ context when multi-vertical is disabled."""
        
        # Load client premises
        premises_result = self.premise_service.ensure_premise_or_fallback(startup_id)
        premises = premises_result.get("premises") if premises_result else None
        
        return ExecutionContext(
            startup_id=startup_id,
            user_id=user_id,
            template_key=template_key,
            partner_id="fcj",
            vertical_id=None,
            method_version="v1.0",
            language_tone="consultative",
            premises=premises,
            governance_gate_refs=[],
            risk_rule_refs=[],
        )


class TemplateSelector:
    """
    Selects templates based on partner/vertical context.
    
    Reuses existing Template Registry, just filters by context.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.config = get_or_create_enterprise_config()
    
    def get_available_templates(
        self,
        context: ExecutionContext
    ) -> List[str]:
        """
        Get available templates for context.
        
        Logic:
        1. If multi_vertical enabled and vertical has template_refs → use them
        2. If multi_vertical enabled but no refs → use all templates
        3. If multi_vertical disabled → use all templates
        """
        
        if not self.config.multi_vertical:
            return self._get_all_templates()
        
        # Load vertical
        vertical_service = VerticalService(self.db)
        vertical = vertical_service.get_vertical(context.vertical_id) if context.vertical_id else None
        
        if vertical and vertical.available_templates:
            return vertical.available_templates
        
        # Fallback: all templates
        return self._get_all_templates()
    
    def _get_all_templates(self) -> List[str]:
        """Get all available templates (fallback)."""
        # TODO: Integrate with existing Template Registry
        return [
            "icp_01",
            "persona_01",
            "value_proposition_01",
            "go_to_market_01",
            "business_model_01",
        ]
    
    def is_template_available(
        self,
        template_key: str,
        context: ExecutionContext
    ) -> bool:
        """Check if template is available in context."""
        available = self.get_available_templates(context)
        return template_key in available
