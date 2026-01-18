"""
Admin Templates Router - Pipeline completo de ingestão FCJ
==========================================================

RESPONSABILIDADE:
Endpoints para ingestão, gestão e consulta de templates Excel FCJ.

PIPELINE COMPLETO (POST /upload):
1. Validar .xlsx
2. Extrair snapshot completo (TemplateSnapshotService)
3. Validar snapshot (obrigatório)
4. Detectar fillable areas (FillableAreaDetector)
5. Persistir storage (TemplateStorage)
6. Computar stats e registry (TemplateRegistry)
7. Salvar DB com versionamento
8. Retornar relatório completo

ENDPOINTS:
- POST   /admin/templates/upload
- GET    /admin/templates
- GET    /admin/templates/{template_id}
- GET    /admin/templates/{template_id}/snapshot
- GET    /admin/templates/{template_id}/context (para RAG)
"""

import logging
import gzip
import json
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.auth import get_current_admin
from db.database import get_db
from db.models import User

# ✅ AJUSTE 4: Import do handler de arquivos grandes
from app.services.large_file_handler import (
    LargeFileConfig, FileValidator, MemoryEfficientSnapshot
)

# Import do core FCJ pipeline
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from app.services.template_snapshot import TemplateSnapshotService, validate_snapshot, SnapshotLoadError, SnapshotValidationError
from app.services.fillable_detector import FillableAreaDetector
from app.services.template_storage import TemplateStorageService
from app.services.template_registry import TemplateRegistry

router = APIRouter(prefix="/admin/templates", tags=["admin-templates"])
logger = logging.getLogger(__name__)


class UploadTemplateQuery(BaseModel):
    cycle: str
    description: Optional[str] = None




@router.post("/upload")
async def upload_template(
    cycle: str,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Pipeline completo de ingestão FCJ
    
    Etapas:
    1. Validar arquivo .xlsx
    2. Extrair snapshot completo + validar
    3. Detectar fillable areas
    4. Persistir storage (versionado por hash)
    5. Registrar no DB
    6. Retornar relatório
    
    Returns:
        Dict com:
        - template_id
        - template_key
        - cycle
        - file_hash_sha256
        - paths (original, snapshot, assets)
        - stats (sheets, cells, fields, etc.)
        - validation_report
        - fields_count
    """
    try:
        logger.info(f"📥 Iniciando ingestão: {file.filename} | cycle={cycle}")
        
        # ✅ AJUSTE 4: Validar tamanho ANTES de ler
        is_valid, error_msg = FileValidator.validate_content_length(
            file.size if hasattr(file, 'size') else None
        )
        if not is_valid:
            raise HTTPException(status_code=413, detail=error_msg)
        
        # 1. Ler arquivo
        content = await file.read()
        
        # ✅ AJUSTE 4: Validar tamanho APÓS ler
        is_valid, error_msg = FileValidator.validate_file_size(content, file.filename)
        if not is_valid:
            raise HTTPException(status_code=413, detail=error_msg)
        
        # 2. Extrair snapshot
        logger.info("📊 Extraindo snapshot completo...")
        try:
            snapshot_service = TemplateSnapshotService()
            snapshot, assets = snapshot_service.extract(content)
        except SnapshotLoadError as e:
            logger.error(f"❌ Falha ao carregar arquivo Excel: {e}")
            raise HTTPException(status_code=400, detail=f"Arquivo Excel inválido: {str(e)}")
        except SnapshotValidationError as e:
            logger.error(f"❌ Snapshot inválido: {e}")
            raise HTTPException(status_code=422, detail=f"Snapshot incompleto: {str(e)}")
        
        logger.info(
            f"✓ Snapshot extraído: {len(snapshot['sheets'])} sheets, "
            f"{sum(len(s['cells']) for s in snapshot['sheets'])} células"
        )
        
        # 4. Validar snapshot (auto-check)
        validation_report = validate_snapshot(snapshot)
        if not validation_report["valid"]:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Snapshot INVÁLIDO - extração incompleta",
                    "errors": validation_report["errors"]
                }
            )
        
        # 5. Detectar fillable areas
        logger.info("🔍 Detectando áreas preenchíveis...")
        detector = FillableAreaDetector()
        candidates = detector.detect(snapshot)
        
        logger.info(f"✓ Detectados {len(candidates)} campos preenchíveis")
        
        # 6. Persistir storage
        logger.info("💾 Salvando storage...")
        registry = TemplateRegistry()
        file_hash = registry.compute_file_hash(content)
        template_key = registry.compute_template_key(file.filename, cycle)
        
        storage = TemplateStorageService()
        save_result = storage.save(
            file_name=file.filename,
            file_bytes=content,
            snapshot_dict=snapshot,
            assets=assets,
            template_key=template_key,
            cycle=cycle,
        )
        
        logger.info(f"✓ Storage salvo: {template_key}/{cycle}/{file_hash[:8]}")
        
        # 7. Computar stats
        fields_payload = [c.to_dict(template_id="pending") for c in candidates]
        stats = registry.compute_stats(snapshot, fields_payload)
        
        # 8. Persistir DB
        logger.info("🗄️ Registrando no banco...")
        td = registry.upsert_template_definition(
            db=db,
            template_key=template_key,
            cycle=cycle,
            file_hash=file_hash,
            original_path=save_result["paths"]["original_path"],
            snapshot_path=save_result["paths"]["snapshot_path"],
            assets_manifest_path=save_result["paths"].get("assets_manifest_path"),
            stats=stats,
        )
        
        # 9. Salvar fields
        fields_final = [c.to_dict(template_id=str(td.id)) for c in candidates]
        registry.replace_fields_for_template(db=db, template_id=td.id, fields=fields_final)
        
        db.commit()
        
        logger.info(f"✅ Ingestão completa: template_id={td.id}")
        
        # 10. Retornar relatório
        return {
            "message": "Template FCJ ingested successfully",
            "template_id": td.id,
            "template_key": template_key,
            "cycle": cycle,
            "file_hash_sha256": file_hash,
            "paths": save_result["paths"],
            "stats": stats,
            "validation_report": validation_report,
            "fields_count": len(fields_final),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na ingestão: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))




@router.get("")
async def list_templates(
    cycle: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Lista templates registrados, opcionalmente por cycle"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
    from app.models.template_definition import TemplateDefinition
    
    try:
        query = db.query(TemplateDefinition)
        if cycle:
            query = query.filter_by(cycle=cycle)
        
        templates = query.order_by(
            TemplateDefinition.cycle, TemplateDefinition.template_key
        ).all()
        
        return [
            {
                "id": t.id,
                "template_key": t.template_key,
                "cycle": t.cycle,
                "file_hash_sha256": t.file_hash_sha256,
                "stats": json.loads(t.stats_json) if t.stats_json else {},
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in templates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}")
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Detalhes completos de um template + fields ordenados"""
    try:
        registry = TemplateRegistry()
        result = registry.get_template_with_fields(db, template_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}/snapshot")
async def get_snapshot(
    template_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Retorna snapshot JSON descompactado"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
    from app.models.template_definition import TemplateDefinition
    
    try:
        td = db.query(TemplateDefinition).filter_by(id=template_id).one_or_none()
        if not td:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        storage = TemplateStorageService()
        snapshot = storage.load_snapshot(td.snapshot_path)
        
        return snapshot
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}/context")
async def get_template_context(
    template_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Retorna contexto otimizado para RAG/Agente TR4CTION
    
    Returns:
        Dict com:
        - template_meta: info básica
        - fillable_fields: campos ordenados com labels/examples
        - phases_summary: agrupamento por phase
    """
    try:
        registry = TemplateRegistry()
        result = registry.get_template_with_fields(db, template_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        # Agrupar por phase
        phases_summary = {}
        for f in result["fields"]:
            phase = f.get("phase") or "other"
            if phase not in phases_summary:
                phases_summary[phase] = []
            phases_summary[phase].append({
                "label": f["label"],
                "type": f["inferred_type"],
                "required": f["required"],
                "example": f["example_value"],
            })
        
        return {
            "template_meta": {
                "id": result["template"]["id"],
                "template_key": result["template"]["template_key"],
                "cycle": result["template"]["cycle"],
                "stats": result["template"]["stats"],
            },
            "fillable_fields": [
                {
                    "field_id": f["field_id"],
                    "sheet": f["sheet_name"],
                    "label": f["label"],
                    "type": f["inferred_type"],
                    "required": f["required"],
                    "example": f["example_value"],
                    "phase": f["phase"],
                    "order": f["order_index"],
                }
                for f in result["fields"]
            ],
            "phases_summary": phases_summary,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
