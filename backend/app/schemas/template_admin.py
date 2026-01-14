from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TemplateUploadResponse(BaseModel):
    template_id: str
    template_key: str
    cycle: str
    version: int
    stats: Dict[str, int]


class TemplateMeta(BaseModel):
    id: str
    template_key: str
    cycle: str
    version: int
    original_filename: str
    snapshot_schema_version: str
    sheets_count: int
    fields_count: int
    created_at: str
    storage_base_path: str
    snapshot_path: str
    assets_manifest_path: Optional[str] = None


class TemplateDetailResponse(BaseModel):
    meta: TemplateMeta
    fields: List[Dict[str, Any]]


class SnapshotResponse(BaseModel):
    snapshot_schema_version: str
    snapshot: Dict[str, Any]
