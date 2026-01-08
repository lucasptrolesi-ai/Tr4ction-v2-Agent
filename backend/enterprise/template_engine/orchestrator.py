"""
Dynamic Template Engine
=======================

Orquestração inteligente de templates:
- Branch logic (se respondeu X, próximo é Y)
- Versionamento de metodologia FCJ
- Customização por vertical
- Fallback para Template Registry atual

IMPORTANTE:
- Não substitui Template Registry
- Atua como CAMADA SUPERIOR
- Templates são declarativos (YAML)
- Compatível com sistema existente

Exemplo declarativo:
```yaml
template_orchestration:
  version: "1.0"
  
  flows:
    icp_first:
      templates:
        - id: "icp_01"
          fields: ["company_size", "industry", "budget"]
          validation_gates: ["size_industry_coherence"]
          next:
            - condition: "company_size == 'small'"
              next_template: "persona_solopreneur_01"
            - condition: "company_size in ['medium', 'large']"
              next_template: "persona_team_01"
  
  verticals:
    saas:
      templates: ["icp_saas", "persona_saas", "market_saas"]
    marketplace:
      templates: ["icp_market", "persona_market"]
```
"""

from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum
import yaml
import logging

logger = logging.getLogger(__name__)


class VerticalType(str, Enum):
    """Tipos de vertical suportados."""
    SAAS = "saas"
    MARKETPLACE = "marketplace"
    INDÚSTRIA = "industria"
    AGRO = "agro"
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    OTHER = "other"


@dataclass
class TemplateNode:
    """Um nó na orquestração de templates."""
    
    template_id: str
    label: str
    required_fields: List[str]
    optional_fields: List[str] = field(default_factory=list)
    validation_gates: List[str] = field(default_factory=list)
    can_be_skipped: bool = False
    depends_on: Optional[List[str]] = None  # Template IDs que devem ser completados antes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "label": self.label,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "validation_gates": self.validation_gates,
            "can_be_skipped": self.can_be_skipped,
            "depends_on": self.depends_on,
        }


@dataclass
class TemplateRoute:
    """Uma rota/fluxo de templates."""
    
    route_id: str
    name: str
    description: str
    templates: List[TemplateNode]
    vertical: VerticalType = VerticalType.SAAS
    method_version: str = "v1.0"
    is_default: bool = False


class DynamicTemplateEngine:
    """Motor de orquestração dinâmica de templates."""
    
    # Routes padrão (podem ser override com YAML)
    DEFAULT_ROUTES = {
        "icp_first": TemplateRoute(
            route_id="icp_first",
            name="ICP-First Flow",
            description="Começa por ICP, depois Persona, depois Market",
            vertical=VerticalType.SAAS,
            is_default=True,
            templates=[
                TemplateNode(
                    template_id="icp_01",
                    label="Ideal Customer Profile",
                    required_fields=["company_size", "industry", "budget"],
                    validation_gates=["non_generic_response"],
                ),
                TemplateNode(
                    template_id="persona_01",
                    label="Persona",
                    required_fields=["pain_points", "goals", "occupation"],
                    depends_on=["icp_01"],
                    validation_gates=["icp_persona_coherence"],
                ),
                TemplateNode(
                    template_id="market_01",
                    label="Market Analysis",
                    required_fields=["tam", "sam", "som"],
                    depends_on=["icp_01"],
                ),
            ],
        ),
    }
    
    def __init__(self, custom_routes: Optional[Dict[str, TemplateRoute]] = None):
        """
        Inicializa engine.
        
        Args:
            custom_routes: Routes customizadas (override do default)
        """
        self.routes = custom_routes or self.DEFAULT_ROUTES
        logger.info(f"✓ Dynamic Template Engine carregado com {len(self.routes)} rotas")
    
    def get_route(self, route_id: str) -> Optional[TemplateRoute]:
        """Retorna uma rota específica."""
        return self.routes.get(route_id)
    
    def get_next_template(
        self,
        route_id: str,
        current_template_id: str,
        completed_fields: Dict[str, Any],
    ) -> Optional[TemplateNode]:
        """
        Retorna próximo template baseado em:
        1. Sequência natural da rota
        2. Branch logic (se aplicável)
        3. Dependências satisfeitas
        
        Args:
            route_id: ID da rota
            current_template_id: Template atual
            completed_fields: Campos já preenchidos (para branch logic)
        
        Returns:
            Próximo TemplateNode ou None se fim
        """
        route = self.get_route(route_id)
        if not route:
            return None
        
        # 1. Encontra posição atual
        current_idx = None
        for i, node in enumerate(route.templates):
            if node.template_id == current_template_id:
                current_idx = i
                break
        
        if current_idx is None:
            return None
        
        # 2. Encontra próximo
        for i in range(current_idx + 1, len(route.templates)):
            next_node = route.templates[i]
            
            # Verifica dependências
            if next_node.depends_on:
                unmet = [d for d in next_node.depends_on if d not in completed_fields]
                if unmet:
                    continue  # Pula templates com dependências não satisfeitas
            
            return next_node
        
        return None  # Fim da rota
    
    def get_route_progress(
        self,
        route_id: str,
        completed_templates: List[str],
    ) -> Dict[str, Any]:
        """
        Retorna progresso em uma rota.
        
        Args:
            route_id: ID da rota
            completed_templates: Templates já completados
        
        Returns:
            Informações de progresso
        """
        route = self.get_route(route_id)
        if not route:
            return {}
        
        progress = {
            "route_id": route_id,
            "total_templates": len(route.templates),
            "completed": len(completed_templates),
            "percentage": (len(completed_templates) / len(route.templates)) * 100,
            "next_templates": [],
        }
        
        # Identifica próximos templates
        for node in route.templates:
            if node.template_id not in completed_templates:
                # Verifica se dependências estão ok
                can_show = True
                if node.depends_on:
                    unmet = [d for d in node.depends_on if d not in completed_templates]
                    can_show = len(unmet) == 0
                
                if can_show:
                    progress["next_templates"].append(node.to_dict())
        
        return progress
    
    def load_routes_from_yaml(self, yaml_path: str):
        """Carrega rotas customizadas de YAML."""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Parse rotas
            self.routes = {}
            for route_data in data.get("routes", []):
                templates = [
                    TemplateNode(
                        template_id=t["template_id"],
                        label=t["label"],
                        required_fields=t.get("required_fields", []),
                        optional_fields=t.get("optional_fields", []),
                        validation_gates=t.get("validation_gates", []),
                        depends_on=t.get("depends_on"),
                    )
                    for t in route_data.get("templates", [])
                ]
                
                route = TemplateRoute(
                    route_id=route_data["route_id"],
                    name=route_data["name"],
                    description=route_data.get("description", ""),
                    templates=templates,
                    vertical=VerticalType(route_data.get("vertical", "saas")),
                    method_version=route_data.get("method_version", "v1.0"),
                    is_default=route_data.get("is_default", False),
                )
                
                self.routes[route.route_id] = route
            
            logger.info(f"✓ Carregadas {len(self.routes)} rotas de {yaml_path}")
        
        except Exception as e:
            logger.error(f"❌ Erro ao carregar routes YAML: {e}")
    
    def get_available_routes(self, vertical: Optional[VerticalType] = None) -> List[TemplateRoute]:
        """Retorna rotas disponíveis (filtrado por vertical se fornecido)."""
        
        if vertical:
            return [r for r in self.routes.values() if r.vertical == vertical]
        
        return list(self.routes.values())
