"""
Partner & Vertical Models - Phase 4
====================================

Data-driven multi-partner & multi-vertical support.
No code duplication, no hardcoded logic - everything is metadata.

Key Principles:
- Single core system
- Configuration over code
- Versioned and auditable
- Fail-safe: works without partner/vertical context
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any, List
from db.database import Base


class Partner(Base):
    """
    Partner definition (FCJ, corporate partner, specific program).
    
    Examples:
    - FCJ (default)
    - Corporate accelerator
    - University entrepreneurship program
    - Government innovation program
    """
    __tablename__ = "partners"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String(50), primary_key=True)  # fcj, partner_corp_x, edu_usp
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Language & Communication
    language_tone = Column(String(50), default="consultative")  # consultative, educational, executive, technical
    brand_identity = Column(JSON)  # Logo URL, colors, etc (optional)
    
    # Method Configuration
    default_method_version = Column(String(20), default="v1.0")
    
    # Feature Flags (optional overrides)
    feature_overrides = Column(JSON)  # Can override global flags per partner
    
    # Audit
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    verticals = relationship("Vertical", back_populates="partner")
    method_profiles = relationship("MethodProfile", back_populates="partner")


class Vertical(Base):
    """
    Vertical definition (SaaS B2B, Marketplace, Agro, Industry, GovTech, etc).
    
    Each vertical can have:
    - Specific templates
    - Specific governance gates
    - Specific risk rules
    - Specific mandatory premises
    """
    __tablename__ = "verticals"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String(50), primary_key=True)  # saas_b2b, marketplace, agro, industry
    partner_id = Column(String(50), ForeignKey("partners.id"), nullable=False)
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Language & Customization
    language_tone_override = Column(String(50))  # Overrides partner tone if set
    
    # Template Configuration
    available_templates = Column(JSON)  # List of template_keys available for this vertical
    template_order = Column(JSON)  # Optional: custom order for templates
    
    # Governance Configuration
    governance_gates_ref = Column(JSON)  # References to gate IDs (not copies)
    risk_rules_ref = Column(JSON)  # References to risk rule IDs
    
    # Mandatory Premises
    mandatory_premise_fields = Column(JSON)  # Fields that must be filled in premises
    
    # Audit
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    partner = relationship("Partner", back_populates="verticals")
    method_profiles = relationship("MethodProfile", back_populates="vertical")


class MethodProfile(Base):
    """
    Method profile: combination of partner + vertical + version.
    
    This is the context that determines:
    - Which templates are available
    - Which governance rules apply
    - Which risk rules apply
    - What language tone to use
    
    Fail-safe: If no profile found, falls back to FCJ default.
    """
    __tablename__ = "method_profiles"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    partner_id = Column(String(50), ForeignKey("partners.id"), nullable=False)
    vertical_id = Column(String(50), ForeignKey("verticals.id"), nullable=True)  # Optional
    
    # Method Configuration
    method_version = Column(String(20), default="v1.0")
    method_name = Column(String(100), default="FCJ Method")
    
    # Effective Language Tone (computed from partner + vertical)
    effective_language_tone = Column(String(50), default="consultative")
    
    # Configuration References (not copies)
    template_refs = Column(JSON)  # List of template_keys
    governance_gate_refs = Column(JSON)  # List of gate IDs
    risk_rule_refs = Column(JSON)  # List of risk rule IDs
    
    # Audit
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    partner = relationship("Partner", back_populates="method_profiles")
    vertical = relationship("Vertical", back_populates="method_profiles")


# Service Layer
class PartnerService:
    """Service for managing partners."""
    
    def __init__(self, db):
        self.db = db
    
    def get_partner(self, partner_id: str) -> Optional[Partner]:
        """Get partner by ID."""
        return self.db.query(Partner).filter(
            Partner.id == partner_id,
            Partner.is_active == True
        ).first()
    
    def get_or_default(self, partner_id: Optional[str] = None) -> Partner:
        """Get partner or return FCJ default."""
        if partner_id:
            partner = self.get_partner(partner_id)
            if partner:
                return partner
        
        # Fallback to FCJ default
        fcj = self.get_partner("fcj")
        if not fcj:
            # Create FCJ default if not exists
            fcj = Partner(
                id="fcj",
                name="FCJ Venture Builder",
                description="Default FCJ method and governance",
                language_tone="consultative",
                default_method_version="v1.0"
            )
            self.db.add(fcj)
            self.db.commit()
        
        return fcj


class VerticalService:
    """Service for managing verticals."""
    
    def __init__(self, db):
        self.db = db
    
    def get_vertical(self, vertical_id: str) -> Optional[Vertical]:
        """Get vertical by ID."""
        return self.db.query(Vertical).filter(
            Vertical.id == vertical_id,
            Vertical.is_active == True
        ).first()
    
    def get_verticals_by_partner(self, partner_id: str) -> List[Vertical]:
        """Get all verticals for a partner."""
        return self.db.query(Vertical).filter(
            Vertical.partner_id == partner_id,
            Vertical.is_active == True
        ).all()


class MethodProfileService:
    """Service for managing method profiles."""
    
    def __init__(self, db):
        self.db = db
    
    def get_profile(
        self,
        partner_id: Optional[str] = None,
        vertical_id: Optional[str] = None,
        method_version: Optional[str] = None
    ) -> Optional[MethodProfile]:
        """Get method profile by context."""
        query = self.db.query(MethodProfile).filter(
            MethodProfile.is_active == True
        )
        
        if partner_id:
            query = query.filter(MethodProfile.partner_id == partner_id)
        if vertical_id:
            query = query.filter(MethodProfile.vertical_id == vertical_id)
        if method_version:
            query = query.filter(MethodProfile.method_version == method_version)
        
        return query.first()
    
    def get_or_create_default(
        self,
        partner_id: Optional[str] = None,
        vertical_id: Optional[str] = None
    ) -> MethodProfile:
        """Get profile or create FCJ default."""
        profile = self.get_profile(partner_id, vertical_id)
        
        if not profile:
            # Create default FCJ profile
            partner_service = PartnerService(self.db)
            partner = partner_service.get_or_default(partner_id)
            
            profile = MethodProfile(
                partner_id=partner.id,
                vertical_id=vertical_id,
                method_version="v1.0",
                method_name="FCJ Method",
                effective_language_tone=partner.language_tone,
                template_refs=[],
                governance_gate_refs=[],
                risk_rule_refs=[]
            )
            self.db.add(profile)
            self.db.commit()
        
        return profile
    
    def compute_effective_tone(
        self,
        partner: Partner,
        vertical: Optional[Vertical] = None
    ) -> str:
        """Compute effective language tone from partner + vertical."""
        if vertical and vertical.language_tone_override:
            return vertical.language_tone_override
        return partner.language_tone
