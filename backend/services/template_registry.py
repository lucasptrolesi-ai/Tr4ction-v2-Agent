"""
Template Registry Service - Descoberta automática de templates

Responsabilidades:
- Descobrir templates disponíveis sem hardcode
- Listar templates por cycle
- Carregar schemas JSON dinamicamente
- Integrar com sistema existente de forma transparente
"""

import os
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from sqlalchemy.orm import Session

from db.models import TemplateDefinition

logger = logging.getLogger(__name__)


# ============================================================
# 📁 CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_GENERATED_DIR = BASE_DIR / "templates" / "generated"
TEMPLATES_IMAGES_DIR = BASE_DIR.parent / "frontend" / "public" / "templates"


# ============================================================
# 🔍 TEMPLATE REGISTRY
# ============================================================

class TemplateRegistry:
    """
    Registry de templates - descoberta automática e dinâmica
    
    Funciona com ou sem banco de dados:
    - Se DB disponível: usa TemplateDefinition como source of truth
    - Se DB não disponível: lê diretamente do filesystem
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
    
    def list_all_templates(self) -> List[Dict]:
        """
        Lista TODOS os templates registrados
        
        Returns:
            Lista de dicts com metadados dos templates
        """
        if self.db:
            return self._list_from_db()
        else:
            return self._list_from_filesystem()
    
    def list_templates_by_cycle(self, cycle: str) -> List[Dict]:
        """
        Lista templates de um cycle específico
        
        Args:
            cycle: Identificador do cycle (Q1, Q2, Q3...)
        
        Returns:
            Lista de templates do cycle
        """
        if self.db:
            return self._list_from_db(cycle)
        else:
            return self._list_from_filesystem(cycle)
    
    def get_template(self, cycle: str, template_key: str) -> Optional[Dict]:
        """
        Busca template específico
        
        Args:
            cycle: Cycle do template
            template_key: Chave do template
        
        Returns:
            Dict com metadados + schema carregado ou None
        """
        if self.db:
            return self._get_from_db(cycle, template_key)
        else:
            return self._get_from_filesystem(cycle, template_key)
    
    def get_template_schema(self, cycle: str, template_key: str) -> Optional[Dict]:
        """
        Carrega schema JSON de um template
        
        Args:
            cycle: Cycle do template
            template_key: Chave do template
        
        Returns:
            Schema JSON completo ou None
        """
        schema_path = TEMPLATES_GENERATED_DIR / cycle / f"{template_key}.json"
        
        if not schema_path.exists():
            logger.warning(f"Schema not found: {schema_path}")
            return None
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading schema {schema_path}: {e}")
            return None
    
    def list_available_cycles(self) -> List[str]:
        """
        Lista todos os cycles disponíveis
        
        Returns:
            Lista de cycles (sorted)
        """
        if self.db:
            try:
                cycles = self.db.query(TemplateDefinition.cycle).distinct().all()
                return sorted([c[0] for c in cycles])
            except Exception as e:
                logger.error(f"Error querying cycles from DB: {e}")
                return self._list_cycles_from_filesystem()
        else:
            return self._list_cycles_from_filesystem()
    
    # --------------------------------------------------------
    # 🗄️ DATABASE-BASED METHODS
    # --------------------------------------------------------
    
    def _list_from_db(self, cycle: Optional[str] = None) -> List[Dict]:
        """Lista templates do banco"""
        try:
            query = self.db.query(TemplateDefinition).filter_by(status="active")
            
            if cycle:
                query = query.filter_by(cycle=cycle)
            
            templates = query.order_by(
                TemplateDefinition.cycle,
                TemplateDefinition.template_key
            ).all()
            
            return [
                {
                    "id": t.id,
                    "cycle": t.cycle,
                    "template_key": t.template_key,
                    "sheet_name": t.sheet_name,
                    "schema_path": t.schema_path,
                    "image_path": t.image_path,
                    "status": t.status,
                    "description": t.description,
                    "field_count": t.field_count,
                }
                for t in templates
            ]
        except Exception as e:
            logger.error(f"Error listing from DB: {e}")
            return []
    
    def _get_from_db(self, cycle: str, template_key: str) -> Optional[Dict]:
        """Busca template no banco"""
        try:
            template = self.db.query(TemplateDefinition).filter_by(
                cycle=cycle,
                template_key=template_key,
                status="active"
            ).first()
            
            if not template:
                return None
            
            # Carregar schema
            schema = self.get_template_schema(cycle, template_key)
            
            return {
                "id": template.id,
                "cycle": template.cycle,
                "template_key": template.template_key,
                "sheet_name": template.sheet_name,
                "schema_path": template.schema_path,
                "image_path": template.image_path,
                "status": template.status,
                "description": template.description,
                "field_count": template.field_count,
                "schema": schema
            }
        except Exception as e:
            logger.error(f"Error getting from DB: {e}")
            return None
    
    # --------------------------------------------------------
    # 📂 FILESYSTEM-BASED METHODS (FALLBACK)
    # --------------------------------------------------------
    
    def _list_cycles_from_filesystem(self) -> List[str]:
        """Lista cycles descobrindo diretórios"""
        if not TEMPLATES_GENERATED_DIR.exists():
            return []
        
        cycles = []
        for item in TEMPLATES_GENERATED_DIR.iterdir():
            if item.is_dir():
                cycles.append(item.name)
        
        return sorted(cycles)
    
    def _list_from_filesystem(self, cycle: Optional[str] = None) -> List[Dict]:
        """Lista templates lendo filesystem"""
        templates = []
        
        if cycle:
            # Buscar apenas em um cycle
            cycle_dir = TEMPLATES_GENERATED_DIR / cycle
            if cycle_dir.exists():
                templates.extend(self._scan_cycle_directory(cycle, cycle_dir))
        else:
            # Buscar em todos os cycles
            for cycle_name in self._list_cycles_from_filesystem():
                cycle_dir = TEMPLATES_GENERATED_DIR / cycle_name
                templates.extend(self._scan_cycle_directory(cycle_name, cycle_dir))
        
        return templates
    
    def _scan_cycle_directory(self, cycle: str, cycle_dir: Path) -> List[Dict]:
        """Escaneia diretório de um cycle"""
        templates = []
        
        for json_file in cycle_dir.glob("*.json"):
            if json_file.name.startswith("_") or json_file.name.startswith("GENERATION"):
                continue  # Skip arquivos especiais
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                
                template_key = json_file.stem
                
                templates.append({
                    "cycle": cycle,
                    "template_key": template_key,
                    "sheet_name": schema.get("sheet_name", template_key),
                    "schema_path": str(json_file.relative_to(BASE_DIR)),
                    "image_path": f"frontend/public/templates/{cycle}/{template_key}.png",
                    "status": "active",
                    "field_count": len(schema.get("fields", [])),
                })
            except Exception as e:
                logger.error(f"Error reading {json_file}: {e}")
                continue
        
        return templates
    
    def _get_from_filesystem(self, cycle: str, template_key: str) -> Optional[Dict]:
        """Busca template no filesystem"""
        schema_path = TEMPLATES_GENERATED_DIR / cycle / f"{template_key}.json"
        
        if not schema_path.exists():
            return None
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            return {
                "cycle": cycle,
                "template_key": template_key,
                "sheet_name": schema.get("sheet_name", template_key),
                "schema_path": str(schema_path.relative_to(BASE_DIR)),
                "image_path": f"frontend/public/templates/{cycle}/{template_key}.png",
                "status": "active",
                "field_count": len(schema.get("fields", [])),
                "schema": schema
            }
        except Exception as e:
            logger.error(f"Error reading {schema_path}: {e}")
            return None


# ============================================================
# 🎯 CONVENIENCE FUNCTIONS (COMPATIBILIDADE)
# ============================================================

def get_registry(db: Optional[Session] = None) -> TemplateRegistry:
    """
    Factory function para criar registry
    
    Args:
        db: Sessão do banco (opcional)
    
    Returns:
        TemplateRegistry configurado
    """
    return TemplateRegistry(db)


def discover_all_templates(db: Optional[Session] = None) -> List[Dict]:
    """
    Descobre todos os templates disponíveis
    
    Args:
        db: Sessão do banco (opcional)
    
    Returns:
        Lista de templates
    """
    registry = get_registry(db)
    return registry.list_all_templates()


def discover_templates_by_cycle(cycle: str, db: Optional[Session] = None) -> List[Dict]:
    """
    Descobre templates de um cycle específico
    
    Args:
        cycle: Identificador do cycle
        db: Sessão do banco (opcional)
    
    Returns:
        Lista de templates do cycle
    """
    registry = get_registry(db)
    return registry.list_templates_by_cycle(cycle)


def load_template_schema(cycle: str, template_key: str, db: Optional[Session] = None) -> Optional[Dict]:
    """
    Carrega schema JSON de um template
    
    Args:
        cycle: Cycle do template
        template_key: Chave do template
        db: Sessão do banco (opcional)
    
    Returns:
        Schema JSON completo ou None
    """
    registry = get_registry(db)
    return registry.get_template_schema(cycle, template_key)
