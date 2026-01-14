"""
FCJ Template Ingestion Module
==============================

Core do produto TR4CTION para ingestão e análise de templates Excel do método FCJ.

Componentes principais:
- TemplateSnapshotService: Extração completa sem perda
- FillableAreaDetector: Detecção inteligente de áreas preenchíveis
- TemplateStorageService: Persistência versionada por hash
- TemplateRegistry: Gestão de ciclo de vida no DB

Uso básico:
    from app.services import (
        TemplateSnapshotService,
        FillableAreaDetector,
        TemplateStorageService,
        TemplateRegistry
    )
    
    # Pipeline completo
    snapshot_service = TemplateSnapshotService()
    snapshot, assets = snapshot_service.extract(file_bytes)
    
    detector = FillableAreaDetector()
    candidates = detector.detect(snapshot)
    
    storage = TemplateStorageService()
    save_result = storage.save(...)
    
    registry = TemplateRegistry()
    template_def = registry.upsert_template_definition(db, ...)
"""

__version__ = "1.0.0"
__author__ = "TR4CTION Team"
__all__ = [
    "TemplateSnapshotService",
    "FillableAreaDetector",
    "TemplateStorageService",
    "TemplateRegistry",
    "validate_snapshot",
    "SnapshotValidationError",
]

# Imports para facilitar uso externo
try:
    from .services.template_snapshot import (
        TemplateSnapshotService,
        validate_snapshot,
        SnapshotValidationError,
        SNAPSHOT_SCHEMA_VERSION
    )
    from .services.fillable_detector import (
        FillableAreaDetector,
        FillableFieldCandidate
    )
    from .services.template_storage import TemplateStorageService
    from .services.template_registry import TemplateRegistry
except ImportError:
    # Fallback para quando módulo é importado de fora do contexto app/
    pass
