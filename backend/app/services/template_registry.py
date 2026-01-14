"""
Template Registry Service - Persistência e versionamento de templates
=====================================================================

RESPONSABILIDADE:
Gerenciar ciclo de vida dos templates no banco de dados,
garantindo versionamento por hash e idempotência.

MODELO:
template_definitions:
  - (template_key, cycle, file_hash) -> UNIQUE
  - paths para storage
  - stats JSON
  - timestamps

fillable_fields:
  - (template_id, field_id) -> UNIQUE
  - metadados semânticos FCJ
  - order_index para consulta ordenada

GARANTIAS:
- Upsert idempotente por hash
- Stats computados automaticamente
- Replace atômico de fields
"""

from __future__ import annotations
import os
import json
import hashlib
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """
    Registry de templates no banco de dados
    """

    def compute_file_hash(self, file_bytes: bytes) -> str:
        """Computa SHA-256 do arquivo"""
        return hashlib.sha256(file_bytes).hexdigest()

    def compute_template_key(self, file_name: str, cycle: str) -> str:
        """
        Computa chave estável do template
        
        Estratégia: base name + cycle (sanitizado)
        """
        base = os.path.splitext(os.path.basename(file_name))[0]
        # Sanitizar
        base = base.lower().replace(" ", "_").replace("-", "_")
        key = f"{cycle.lower()}_{base}"
        return key

    def compute_stats(
        self,
        snapshot: Dict[str, Any],
        fields: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Computa estatísticas do template
        
        Returns:
            Dict com contadores relevantes
        """
        sheets = snapshot.get("sheets", [])
        
        stats = {
            "num_sheets": len(sheets),
            "num_cells": sum(len(s.get("cells", [])) for s in sheets),
            "num_merged": sum(len(s.get("merged_cells", [])) for s in sheets),
            "num_images": sum(len(s.get("images", [])) for s in sheets),
            "num_validations": sum(len(s.get("data_validations", [])) for s in sheets),
            "num_tables": sum(len(s.get("tables", [])) for s in sheets),
            "num_fields": len(fields),
            "schema_version": snapshot.get("schema_version"),
        }
        
        return stats

    def upsert_template_definition(
        self,
        db: Session,
        template_key: str,
        cycle: str,
        file_hash: str,
        original_path: str,
        snapshot_path: str,
        assets_manifest_path: Optional[str],
        stats: Dict[str, Any]
    ):
        """
        Insere ou atualiza definição do template
        
        Idempotência: (template_key, cycle, file_hash) é UNIQUE
        
        Returns:
            TemplateDefinition instance
        """
        from ..models.template_definition import TemplateDefinition
        
        # Buscar existente
        existing = db.query(TemplateDefinition).filter_by(
            template_key=template_key,
            cycle=cycle,
            file_hash_sha256=file_hash
        ).one_or_none()
        
        if existing:
            # Atualizar paths (caso tenha mudado)
            existing.original_path = original_path
            existing.snapshot_path = snapshot_path
            existing.assets_manifest_path = assets_manifest_path
            existing.stats_json = json.dumps(stats)
            existing.updated_at = datetime.utcnow()
            db.flush()
            
            logger.info(f"✓ Template atualizado: {template_key}/{cycle} (id={existing.id})")
            return existing
        
        # Criar novo
        td = TemplateDefinition(
            template_key=template_key,
            cycle=cycle,
            file_hash_sha256=file_hash,
            original_path=original_path,
            snapshot_path=snapshot_path,
            assets_manifest_path=assets_manifest_path,
            stats_json=json.dumps(stats),
        )
        db.add(td)
        db.flush()
        
        logger.info(f"✓ Template criado: {template_key}/{cycle} (id={td.id})")
        return td

    def replace_fields_for_template(
        self,
        db: Session,
        template_id: int,
        fields: List[Dict[str, Any]]
    ):
        """
        Substitui todos os fields de um template
        
        Operação atômica: delete all + insert new
        
        Args:
            db: Session
            template_id: ID do template
            fields: Lista de dicts com dados dos fields
        """
        from ..models.template_definition import FillableField
        
        # Delete existentes
        deleted = db.query(FillableField).filter_by(template_id=template_id).delete()
        
        # Insert novos
        for f in fields:
            ff = FillableField(
                template_id=template_id,
                field_id=f.get("field_id"),
                sheet_name=f.get("sheet_name"),
                cell_range=f.get("cell_range"),
                label=f.get("label"),
                inferred_type=f.get("inferred_type"),
                required=bool(f.get("required", True)),
                example_value=f.get("example_value"),
                phase=f.get("phase"),
                order_index=int(f.get("order_index", 0)),
                source_metadata_json=json.dumps(f.get("source_metadata", {}))
            )
            db.add(ff)
        
        db.flush()
        
        logger.info(
            f"✓ Fields substituídos: template_id={template_id}, "
            f"{deleted} deletados, {len(fields)} inseridos"
        )

    def get_template_with_fields(
        self,
        db: Session,
        template_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Busca template completo com fields ordenados
        
        Returns:
            Dict com template + fields ou None
        """
        from ..models.template_definition import TemplateDefinition, FillableField
        
        td = db.query(TemplateDefinition).filter_by(id=template_id).one_or_none()
        if not td:
            return None
        
        fields = db.query(FillableField).filter_by(
            template_id=template_id
        ).order_by(FillableField.order_index.asc()).all()
        
        return {
            "template": {
                "id": td.id,
                "template_key": td.template_key,
                "cycle": td.cycle,
                "file_hash_sha256": td.file_hash_sha256,
                "original_path": td.original_path,
                "snapshot_path": td.snapshot_path,
                "assets_manifest_path": td.assets_manifest_path,
                "stats": json.loads(td.stats_json) if td.stats_json else {},
                "created_at": td.created_at.isoformat() if td.created_at else None,
                "updated_at": td.updated_at.isoformat() if td.updated_at else None,
            },
            "fields": [
                {
                    "id": f.id,
                    "field_id": f.field_id,
                    "sheet_name": f.sheet_name,
                    "cell_range": f.cell_range,
                    "label": f.label,
                    "inferred_type": f.inferred_type,
                    "required": f.required,
                    "example_value": f.example_value,
                    "phase": f.phase,
                    "order_index": f.order_index,
                    "source_metadata": json.loads(f.source_metadata_json) if f.source_metadata_json else {},
                }
                for f in fields
            ]
        }
