from __future__ import annotations
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..services.template_snapshot import TemplateSnapshotService
from ..services.template_storage import TemplateStorageService
from ..services.fillable_detector import FillableAreaDetector
from ..services.template_registry import TemplateRegistry

router = APIRouter(prefix="/admin/templates", tags=["admin-templates"])


def ensure_is_admin():
    # TODO: integrate with real auth in services/auth.py
    # For now, assume request is authenticated and authorized by existing middleware
    return True


@router.post("/upload")
async def upload_template(file: UploadFile = File(...), db: Session = Depends(get_db), _admin=Depends(ensure_is_admin)):
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Somente arquivos .xlsx são suportados")
    content = await file.read()

    # Extract snapshot
    snap_service = TemplateSnapshotService()
    snapshot, assets = snap_service.extract(content)

    # Detect fillable fields
    detector = FillableAreaDetector()
    candidates = detector.detect(snapshot)

    # Persist storage
    storage = TemplateStorageService()
    save_res = storage.save(
        file_name=file.filename,
        file_bytes=content,
        snapshot_dict=snapshot,
        assets=assets,
    )

    # Registry persistence
    registry = TemplateRegistry()
    file_hash = registry.compute_file_hash(content)
    template_key = registry.compute_template_key(file.filename)
    fields_payload = [c.to_dict(template_id="pending") for c in candidates]
    stats = registry.compute_stats(snapshot, fields_payload)

    td = registry.upsert_template_definition(
        db=db,
        template_key=template_key,
        cycle="default",
        file_hash=file_hash,
        original_path=save_res["paths"]["original_path"],
        snapshot_path=save_res["paths"]["snapshot_path"],
        assets_manifest_path=save_res["paths"].get("assets_manifest_path"),
        stats=stats,
    )

    # Now write fields with real template_id
    fields_final = [c.to_dict(template_id=str(td.id)) for c in candidates]
    registry.replace_fields_for_template(db=db, template_id=td.id, fields=fields_final)

    return {
        "template_id": td.id,
        "template_key": template_key,
        "cycle": "default",
        "file_hash_sha256": file_hash,
        "paths": save_res["paths"],
        "stats": stats,
        "num_fields": len(fields_final)
    }


@router.get("/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db), _admin=Depends(ensure_is_admin)):
    from ..models.template_definition import TemplateDefinition, FillableField
    td = db.query(TemplateDefinition).filter_by(id=template_id).one_or_none()
    if not td:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    fields = db.query(FillableField).filter_by(template_id=template_id).order_by(FillableField.order_index.asc()).all()
    return {
        "template": {
            "id": td.id,
            "template_key": td.template_key,
            "cycle": td.cycle,
            "file_hash_sha256": td.file_hash_sha256,
            "paths": {
                "original_path": td.original_path,
                "snapshot_path": td.snapshot_path,
                "assets_manifest_path": td.assets_manifest_path,
            },
            "stats": td.stats_json,
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
                "source_metadata": f.source_metadata_json,
            } for f in fields
        ]
    }


@router.get("/{template_id}/snapshot")
def get_snapshot(template_id: int, db: Session = Depends(get_db), _admin=Depends(ensure_is_admin)):
    from ..models.template_definition import TemplateDefinition
    td = db.query(TemplateDefinition).filter_by(id=template_id).one_or_none()
    if not td:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    path = td.snapshot_path
    import gzip, json
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler snapshot: {e}")
    return data
