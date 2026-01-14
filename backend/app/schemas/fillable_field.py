from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Dict, Any


class FillableFieldSchema(BaseModel):
    id: str
    template_id: str
    field_id: str
    sheet_name: str
    cell_range: str
    label: Optional[str]
    inferred_type: str
    required: bool
    example_value: Optional[str]
    phase: Optional[str]
    order_index: int
    source_metadata: Optional[Dict[str, Any]]
