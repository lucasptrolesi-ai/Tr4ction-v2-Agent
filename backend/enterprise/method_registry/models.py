"""
Method Registry & Verticalization
===================================

Suporta múltiplas verticais e versões do método FCJ.

Contexto:
- O método FCJ evoluiu muito em 5 anos
- Cada vertical (SaaS, Marketplace, Indústria) tem variações
- Sistema precisa de versionamento explícito
- Compatibilidade retroativa é importante

Estrutura:
```
method_registry/
  fcj/
    v1.0/  (original)
      saas/
        templates.yaml
        rules.yaml
      marketplace/
        templates.yaml
    v1.5/  (evolução)
      saas/
        templates.yaml
```
"""

from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
from enum import Enum
import yaml
import logging

logger = logging.getLogger(__name__)


class VerticalType(str, Enum):
    """Tipos de vertical suportados."""
    SAAS = "saas"
    MARKETPLACE = "marketplace"
    INDUSTRIA = "industria"
    AGRO = "agro"
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"


@dataclass
class MethodVersion:
    """Uma versão do método FCJ."""
    
    version: str  # Ex: "v1.0", "v1.5", "v2.0"
    release_date: str
    description: str
    supported_verticals: List[VerticalType]
    breaking_changes: Optional[List[str]] = None
    notes: Optional[str] = None
    deprecated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "release_date": self.release_date,
            "description": self.description,
            "supported_verticals": [v.value for v in self.supported_verticals],
            "breaking_changes": self.breaking_changes,
            "notes": self.notes,
            "deprecated": self.deprecated,
        }


class MethodRegistry:
    """Registry central de versões e verticais do método FCJ."""
    
    # Versões disponíveis
    AVAILABLE_VERSIONS = {
        "v1.0": MethodVersion(
            version="v1.0",
            release_date="2024-01-01",
            description="Versão original do método FCJ",
            supported_verticals=[VerticalType.SAAS],
            notes="Baseline - compatibilidade com FCJ clássico",
        ),
        "v1.5": MethodVersion(
            version="v1.5",
            release_date="2024-06-01",
            description="Adição de suporte a Marketplaces e Indústria",
            supported_verticals=[
                VerticalType.SAAS,
                VerticalType.MARKETPLACE,
                VerticalType.INDUSTRIA,
            ],
            notes="Melhorias em templates de ICP e Persona",
        ),
        "v2.0": MethodVersion(
            version="v2.0",
            release_date="2025-01-01",
            description="Versão enterprise com suporte a mais verticais",
            supported_verticals=[
                VerticalType.SAAS,
                VerticalType.MARKETPLACE,
                VerticalType.INDUSTRIA,
                VerticalType.AGRO,
                VerticalType.FINTECH,
                VerticalType.HEALTHTECH,
            ],
            breaking_changes=[
                "Templates.json schema mudou",
                "Rules.yaml estrutura renovada",
            ],
            notes="Versão atual recomendada",
        ),
    }
    
    # Mapeamento de vertical → templates específicos
    VERTICAL_CUSTOMIZATIONS = {
        VerticalType.SAAS: {
            "icp_template": "icp_saas",
            "persona_template": "persona_saas",
            "market_template": "market_saas",
            "extra_templates": ["pricing_saas", "gtm_saas"],
        },
        VerticalType.MARKETPLACE: {
            "icp_template": "icp_market",
            "persona_template": "persona_market_supplier",  # supplier + buyer
            "market_template": "market_market",
            "extra_templates": ["network_effects", "supply_demand_balance"],
        },
        VerticalType.INDUSTRIA: {
            "icp_template": "icp_industria",
            "persona_template": "persona_industria_cfo",  # Geralmente CFO
            "market_template": "market_industria",
            "extra_templates": ["supply_chain", "manufacturing_unit_economics"],
        },
        VerticalType.AGRO: {
            "icp_template": "icp_agro",
            "persona_template": "persona_agro_farmer",
            "market_template": "market_agro",
            "extra_templates": ["seasonality", "commodity_exposure"],
        },
    }
    
    def __init__(self):
        logger.info(f"✓ Method Registry initialized com {len(self.AVAILABLE_VERSIONS)} versões")
    
    def get_version(self, version: str) -> Optional[MethodVersion]:
        """Retorna uma versão específica."""
        return self.AVAILABLE_VERSIONS.get(version)
    
    def get_latest_version(self) -> MethodVersion:
        """Retorna versão mais recente."""
        return self.AVAILABLE_VERSIONS["v2.0"]
    
    def get_available_versions(self) -> List[MethodVersion]:
        """Retorna todas as versões disponíveis."""
        return list(self.AVAILABLE_VERSIONS.values())
    
    def is_version_compatible_with_vertical(
        self,
        version: str,
        vertical: VerticalType,
    ) -> bool:
        """Verifica se versão suporta vertical."""
        
        method_version = self.get_version(version)
        if not method_version:
            return False
        
        return vertical in method_version.supported_verticals
    
    def get_templates_for_vertical(
        self,
        vertical: VerticalType,
        version: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Retorna templates específicos de uma vertical.
        
        Args:
            vertical: Tipo de vertical
            version: Versão do método (default: latest)
        
        Returns:
            Dicionário com mapeamento de templates
        """
        
        if version is None:
            version = "v2.0"
        
        # Valida compatibilidade
        if not self.is_version_compatible_with_vertical(version, vertical):
            logger.warning(f"⚠ Versão {version} não suporta vertical {vertical.value}")
            return {}
        
        return self.VERTICAL_CUSTOMIZATIONS.get(vertical, {})
    
    def get_vertical_specific_rules(
        self,
        vertical: VerticalType,
        version: str = "v2.0",
    ) -> Dict[str, Any]:
        """
        Retorna regras de governança específicas de uma vertical.
        
        Exemplo: Marketplace precisa validar "supplier" e "buyer" personas.
        """
        
        if vertical == VerticalType.MARKETPLACE:
            return {
                "requires_dual_persona": True,
                "personas": ["supplier", "buyer"],
                "min_suppliers": 5,
                "min_buyers": 10,
                "coherence_check": "supplier_value + buyer_value must align",
            }
        
        elif vertical == VerticalType.AGRO:
            return {
                "requires_seasonality_plan": True,
                "risk_factors": ["commodity_price", "weather", "crop_disease"],
                "cash_flow_critical": True,
            }
        
        return {}
    
    def suggest_migration_path(
        self,
        current_version: str,
        target_vertical: VerticalType,
    ) -> Optional[Dict[str, Any]]:
        """
        Sugere caminho de migração se necessário.
        
        Ex: Se startup em v1.0 quer usar Marketplace (v1.5+),
        retorna recomendações de upgrade.
        """
        
        current = self.get_version(current_version)
        if not current:
            return None
        
        # Se já é compatível, sem migração necessária
        if target_vertical in current.supported_verticals:
            return {"migration_needed": False}
        
        # Encontra versão mínima que suporta vertical
        for version in self.get_available_versions():
            if target_vertical in version.supported_verticals:
                if version.version > current_version:
                    return {
                        "migration_needed": True,
                        "recommended_version": version.version,
                        "breaking_changes": version.breaking_changes,
                        "notes": version.notes,
                    }
        
        return None
