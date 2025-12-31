"""
Admin Templates Use Case - Lógica de negócio para gerenciamento de templates

Responsabilidades:
- Coordenar upload e ingestão de templates
- Listar templates por cycle
- Ativar/desativar templates
- Buscar templates individuais
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from services.template_ingestion_service import TemplateIngestionService
from db.models import TemplateDefinition

logger = logging.getLogger(__name__)


async def upload_and_ingest_template(
    file_content: bytes,
    filename: str,
    cycle: str,
    description: Optional[str],
    db: Session
) -> Dict:
    """
    Processa upload e ingestão de arquivo Excel de templates
    
    Args:
        file_content: Conteúdo binário do arquivo
        filename: Nome original do arquivo
        cycle: Identificador do cycle (Q1, Q2, Q3...)
        description: Descrição opcional
        db: Sessão do banco de dados
    
    Returns:
        Dict com estatísticas da ingestão
    """
    try:
        # Instanciar serviço
        service = TemplateIngestionService(db)
        
        # Salvar arquivo
        file_path = service.save_uploaded_file(file_content, filename, cycle)
        logger.info(f"File saved: {file_path}")
        
        # Executar ingestão
        result = service.ingest_excel_file(file_path, cycle, description)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in upload_and_ingest_template: {e}", exc_info=True)
        raise


def list_templates_by_cycle(cycle: Optional[str], db: Session) -> List[Dict]:
    """
    Lista templates registrados, opcionalmente filtrados por cycle
    
    Args:
        cycle: Cycle para filtrar (None = todos)
        db: Sessão do banco de dados
    
    Returns:
        Lista de templates
    """
    try:
        query = db.query(TemplateDefinition)
        
        if cycle:
            query = query.filter(TemplateDefinition.cycle == cycle)
        
        # Ordenar por cycle e template_key
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
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in templates
        ]
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        raise


def get_template_by_key(cycle: str, template_key: str, db: Session) -> Optional[Dict]:
    """
    Busca template específico por cycle e template_key
    
    Args:
        cycle: Cycle do template
        template_key: Chave do template
        db: Sessão do banco de dados
    
    Returns:
        Dict com dados do template ou None
    """
    try:
        template = db.query(TemplateDefinition).filter_by(
            cycle=cycle,
            template_key=template_key
        ).first()
        
        if not template:
            return None
        
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
            "source_file": template.source_file,
            "ingestion_report": template.ingestion_report,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
        }
        
    except Exception as e:
        logger.error(f"Error getting template: {e}", exc_info=True)
        raise


def update_template_status(
    template_id: int,
    status: str,
    db: Session
) -> Dict:
    """
    Atualiza status de um template (active/inactive/archived)
    
    Args:
        template_id: ID do template
        status: Novo status
        db: Sessão do banco de dados
    
    Returns:
        Template atualizado
    """
    try:
        template = db.query(TemplateDefinition).filter_by(id=template_id).first()
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        template.status = status
        db.commit()
        db.refresh(template)
        
        logger.info(f"Updated template {template_id} status to '{status}'")
        
        return {
            "id": template.id,
            "cycle": template.cycle,
            "template_key": template.template_key,
            "status": template.status,
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating template status: {e}", exc_info=True)
        raise


def list_available_cycles(db: Session) -> List[str]:
    """
    Lista todos os cycles disponíveis (distinct)
    
    Returns:
        Lista de cycles
    """
    try:
        cycles = db.query(TemplateDefinition.cycle).distinct().all()
        return sorted([c[0] for c in cycles])
        
    except Exception as e:
        logger.error(f"Error listing cycles: {e}", exc_info=True)
        raise
