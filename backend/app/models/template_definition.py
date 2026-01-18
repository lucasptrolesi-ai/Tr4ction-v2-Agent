from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean, JSON, Index
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.orm import relationship

from db.database import Base


class TemplateDefinition(Base):
    __tablename__ = "template_definitions"
    __table_args__ = (
        Index("ix_template_key_cycle_hash", "template_key", "cycle", "file_hash_sha256", unique=True),
        {"extend_existing": True},
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_key = Column(String, index=True, nullable=False)
    cycle = Column(String, index=True, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    file_hash_sha256 = Column(String(64), index=True, nullable=False)
    original_filename = Column(String, nullable=False)

    storage_base_path = Column(Text, nullable=False)
    snapshot_path = Column(Text, nullable=False)
    snapshot_schema_version = Column(String, nullable=False, default="1.0")
    assets_manifest_path = Column(Text, nullable=True)

    sheets_count = Column(Integer, nullable=False, default=0)
    fields_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    fields = relationship("FillableField", back_populates="template", cascade="all, delete-orphan")


class FillableField(Base):
    __tablename__ = "fillable_fields"
    __table_args__ = (
        Index("ix_template_sheet", "template_id", "sheet_name"),
        Index("ix_template_phase", "template_id", "phase"),
        Index("ix_template_order", "template_id", "order_index"),
        # ✅ AJUSTE 1: Unicidade composta (template_id + field_id) - não global
        Index("uq_field_per_template", "template_id", "field_id", unique=True),
        {"extend_existing": True},
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String, ForeignKey("template_definitions.id"), index=True, nullable=False)

    # ✅ AJUSTE 1: field_id é único POR TEMPLATE, não globalmente
    field_id = Column(String, index=True, nullable=False)
    sheet_name = Column(String, index=True, nullable=False)
    cell_range = Column(String, nullable=False)
    label = Column(Text, nullable=True)
    inferred_type = Column(String, nullable=False)
    required = Column(Boolean, default=True, nullable=False)
    example_value = Column(Text, nullable=True)
    phase = Column(String, index=True, nullable=True)
    order_index = Column(Integer, index=True, nullable=False, default=0)
    source_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    template = relationship("TemplateDefinition", back_populates="fields")
