"""
Template Router
===============
FastAPI endpoints for template management.

Routes:
- GET  /founder/templates/{template_key}
  → Load template schema + saved data
  
- POST /founder/templates/{template_key}
  → Save founder's template response
  
- POST /founder/templates/{template_key}/export
  → Export filled template to Excel
  
- GET  /founder/templates/{template_key}/versions
  → List all saved versions of a template
  
- POST /founder/templates/{template_key}/ai-mentor
  → Send template context to AI mentor chat

All endpoints are generic and work for any template.
Authentication: requires JWT with founder or admin role.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from services.auth import get_current_user_required
from db.models import User
from services.template_manager import TemplateManager, TemplateDataService

logger = logging.getLogger(__name__)

# Initialize services
template_data_service = TemplateDataService()
template_manager = TemplateManager(template_data_service)

router = APIRouter(prefix="/templates", tags=["templates"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TemplateFieldResponse(BaseModel):
    """Single template field."""
    key: str
    cell: str
    type: str
    label: Optional[str] = None
    placeholder: Optional[str] = None
    required: bool = False
    section: Optional[str] = None
    help_text: Optional[str] = None
    position: Dict[str, float]  # {top, left, width, height}
    validation_rules: Dict[str, Any] = {}


class TemplateSchemaResponse(BaseModel):
    """Template schema for frontend rendering."""
    template_key: str
    sheet_name: str
    sheet_width: float
    sheet_height: float
    title: Optional[str] = None
    description: Optional[str] = None
    version: str
    fields: list[TemplateFieldResponse]


class TemplateSavedDataResponse(BaseModel):
    """Saved template data."""
    template_key: str
    startup_id: str
    data: Dict[str, Any]
    created_at: str
    updated_at: str
    version: int


class TemplateResponse(BaseModel):
    """Combined template schema + saved data."""
    template_schema: TemplateSchemaResponse = Field(..., alias="schema")
    saved_data: Optional[TemplateSavedDataResponse] = None
    versions: list[TemplateSavedDataResponse] = []
    
    model_config = {"populate_by_name": True}


class TemplateDataRequest(BaseModel):
    """Founder's template response."""
    data: Dict[str, Any] = Field(
        ...,
        example={
            "persona_name": "Young Urban Professional",
            "age_range": "25-35",
            "occupation": "Software Engineer"
        }
    )


class TemplateValidationError(BaseModel):
    """Validation error detail."""
    field: str
    message: str


class TemplateValidationResponse(BaseModel):
    """Validation result."""
    valid: bool
    errors: list[TemplateValidationError] = []
    warnings: list[TemplateValidationError] = []


class ExportResponse(BaseModel):
    """Export result."""
    message: str
    file_url: str
    startup_id: str
    template_key: str


class AIMentorPayload(BaseModel):
    """Payload sent to AI mentor chat."""
    template_key: str
    sheet_name: str
    template_title: Optional[str] = None
    current_field: Optional[str] = None
    field_label: Optional[str] = None
    template_data: Dict[str, Any]
    all_fields: list[Dict[str, Any]]  # Schema fields for context
    previous_templates: Optional[Dict[str, Any]] = None  # Data from related templates


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_founder(user: User = Depends(get_current_user_required)) -> User:
    """Ensure user is founder or admin."""
    if user.role not in ["founder", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only founders can access templates"
        )
    return user


def get_user_startup_id(user: User = Depends(get_current_founder)) -> str:
    """Get startup ID from user context."""
    # TODO: This should come from user.startup_id or inferred from context
    # For now, use user.id as a placeholder
    return str(user.id)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/{template_key}",
    response_model=TemplateResponse,
    summary="Get Template Schema + Saved Data",
    description="Load template schema and any saved data for the founder"
)
async def get_template(
    template_key: str,
    startup_id: str = Depends(get_user_startup_id),
    user: User = Depends(get_current_founder),
):
    """
    Get template schema and saved data.
    
    Returns:
    - schema: Full template structure with fields and positions
    - saved_data: Previous founder response (if exists)
    - versions: All saved versions for comparison/history
    """
    try:
        template = template_manager.get_template_for_founder(startup_id, template_key)
        
        logger.info(f"Retrieved template {template_key} for {startup_id}")
        
        return TemplateResponse(
            schema=TemplateSchemaResponse(**template["schema"]),
            saved_data=template["saved_data"],
            versions=template["versions"]
        )
    
    except FileNotFoundError as e:
        logger.error(f"Template not found: {template_key}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_key}' not found"
        )
    except Exception as e:
        logger.error(f"Error loading template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/{template_key}",
    response_model=TemplateSavedDataResponse,
    status_code=status.HTTP_200_OK,
    summary="Save Template Response",
    description="Save founder's template responses"
)
async def save_template(
    template_key: str,
    request: TemplateDataRequest,
    startup_id: str = Depends(get_user_startup_id),
    user: User = Depends(get_current_founder),
):
    """
    Save founder's template response.
    
    Validates data against schema before saving.
    Auto-increments version on each save.
    """
    try:
        # Validate
        validation = template_data_service.validate_data(template_key, request.data)
        
        if not validation["valid"]:
            logger.warning(f"Validation failed for {template_key}: {validation['errors']}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Validation failed",
                    "errors": validation["errors"]
                }
            )
        
        # Save
        saved = template_data_service.save_template_data(
            startup_id=startup_id,
            template_key=template_key,
            data=request.data,
            auto_version=True
        )
        
        logger.info(f"Saved template {template_key} v{saved['version']} for {startup_id}")
        
        return TemplateSavedDataResponse(**saved)
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_key}' not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error saving template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{template_key}/versions",
    response_model=list[TemplateSavedDataResponse],
    summary="List Template Versions",
    description="Get all saved versions of a template for the founder"
)
async def list_versions(
    template_key: str,
    startup_id: str = Depends(get_user_startup_id),
    user: User = Depends(get_current_founder),
):
    """List all versions of a template for history/comparison."""
    try:
        versions = template_data_service.list_template_versions(startup_id, template_key)
        return versions
    except Exception as e:
        logger.error(f"Error listing versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/{template_key}/export",
    response_model=ExportResponse,
    summary="Export to Excel",
    description="Export filled template to Excel file"
)
async def export_template(
    template_key: str,
    startup_id: str = Depends(get_user_startup_id),
    user: User = Depends(get_current_founder),
):
    """
    Export template data back to Excel.
    
    Creates a new Excel file with:
    - All filled field values in original cells
    - Light yellow highlight on filled cells
    - Metadata sheet with export info
    """
    try:
        # TODO: This should come from config
        EXCEL_TEMPLATES_DIR = Path("data/excel_templates")
        original_excel = EXCEL_TEMPLATES_DIR / "Template Q1.xlsx"
        
        if not original_excel.exists():
            raise FileNotFoundError(f"Template file not found: {original_excel}")
        
        # Export
        excel_path = template_manager.export_founder_template(
            startup_id=startup_id,
            template_key=template_key,
            original_excel_path=original_excel,
            output_dir="exports"
        )
        
        # Build download URL
        # TODO: Adjust based on your static file serving setup
        file_url = f"/api/downloads/{excel_path.name}"
        
        logger.info(f"Exported {template_key} for {startup_id} to {excel_path}")
        
        return ExportResponse(
            message="Export successful",
            file_url=file_url,
            startup_id=startup_id,
            template_key=template_key
        )
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error exporting template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/{template_key}/ai-mentor",
    response_model=AIMentorPayload,
    summary="Prepare AI Mentor Payload",
    description="Prepare template context for AI mentor chat"
)
async def prepare_ai_mentor_payload(
    template_key: str,
    current_field: Optional[str] = None,
    startup_id: str = Depends(get_user_startup_id),
    user: User = Depends(get_current_founder),
):
    """
    Prepare payload to send to AI mentor.
    
    Includes:
    - Template schema and user data
    - Previous related templates (for coherence checking)
    - Current field context (if applicable)
    """
    try:
        # Load template
        template = template_manager.get_template_for_founder(startup_id, template_key)
        schema = template["schema"]
        saved_data = template["saved_data"]
        
        # Get field label if field specified
        field_label = None
        if current_field:
            for field in schema["fields"]:
                if field["key"] == current_field:
                    field_label = field.get("label", current_field)
                    break
        
        # TODO: Load previous related templates for coherence validation
        # For example: if current is "persona_01", load "icp_01", "market_01"
        previous_templates = None
        
        payload = AIMentorPayload(
            template_key=template_key,
            sheet_name=schema["sheet_name"],
            template_title=schema.get("title"),
            current_field=current_field,
            field_label=field_label,
            template_data=saved_data["data"] if saved_data else {},
            all_fields=[
                {
                    "key": f["key"],
                    "label": f.get("label"),
                    "type": f["type"],
                    "required": f.get("required", False),
                    "section": f.get("section"),
                }
                for f in schema["fields"]
            ],
            previous_templates=previous_templates
        )
        
        logger.info(f"Prepared AI mentor payload for {template_key}")
        
        return payload
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_key}' not found"
        )
    except Exception as e:
        logger.error(f"Error preparing AI mentor payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/health",
    tags=["health"],
    summary="Template Service Health"
)
async def health():
    """Check template service health."""
    return {
        "status": "healthy",
        "service": "template-manager",
        "schemas_available": len(list(template_data_service.schemas_dir.glob("*.json")))
    }
