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

from sqlalchemy.orm import Session

from services.auth import get_current_user_required
from db.models import User
from services.template_manager import TemplateManager, TemplateDataService
from db.database import get_db
from backend.enterprise.client_premises import ClientPremiseService
from backend.enterprise.ai_audit.models import AIAuditService
from backend.enterprise.config import get_or_create_enterprise_config
from backend.enterprise.governance.engine import GovernanceEngine
from backend.enterprise.governance.models import GovernanceGateService
from backend.enterprise.risk_engine.detector import RiskDetectionEngine, RiskClassification
from backend.enterprise.risk_engine.models import RiskSignalService
from backend.enterprise.decision_ledger.models import DecisionLedgerService

logger = logging.getLogger(__name__)

# Initialize services
            startup_id=startup_id,
            template_key=template_key,
            data=request.data,
            auto_version=True
        )

        # Decision ledger (append-only) with governance/risk context
        ledger_service = DecisionLedgerService(db)
        ledger_service.record_decision(
            user_id=str(user.id),
            user_email=getattr(user, "email", ""),
            startup_id=startup_id,
            template_key=template_key,
            field_key="template_save",
            new_value=request.data,
            previous_value=previous_data,
            field_label=None,
            reasoning=None,
            source="founder",
            step_id=None,
            fcj_method_version="v1.0",
            cycle=None,
            related_template_snapshot=None,
            vertical=None,
            premises_used=[premises_payload] if premises_payload else None,
            ai_recommendation=None,
            risk_level=risk_result_dict.get("overall_risk") if risk_result_dict else None,
            human_confirmation=None,
            governance_result=governance_results if governance_results else None,
            risk_result=risk_result_dict,
        )

        # Audit log (if enabled)
        if config.ai_audit:
            try:
                audit_service = AIAuditService(db)
                audit_service.log_event(
                    user_id=str(user.id),
                    startup_id=startup_id,
                    event_type="decision_governance_risk",
                    model="n/a",
                    model_version=None,
                    prompt_hash=None,
                    prompt_version=None,
                    system_prompt_hash=None,
                    system_prompt_version=None,
                    input_tokens={"template_key": template_key},
                    tokens_used=None,
                    response_length=None,
                    latency_ms=None,
                    rules_version=str(governance_results[0].get("gate_version")) if governance_results else None,
                    validation_rules_applied=None,
                    governance_rules_active=[g.get("gate_id") for g in governance_results] if governance_results else None,
                    success=1,
                    error_message=None,
                    template_key=template_key,
                    context_snapshot={
                        "premises_status": premises_status,
                        "risk": risk_result_dict,
                        "governance": governance_results,
                    },
                )
            except Exception as audit_exc:
                logger.warning(f"Audit log skipped: {audit_exc}")
class TemplateValidationError(BaseModel):
        return TemplateSavedDataResponse(**saved, cognitive_signals=cognitive_signals)
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
    client_premises: Optional[Dict[str, Any]] = None
    premises_status: Optional[str] = None


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
    db: Session = Depends(get_db),
):
    """
    Save founder's template response.
    
    Validates data against schema before saving.
    Auto-increments version on each save.
    """
    try:
        config = get_or_create_enterprise_config()

        # Validate against schema
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

        # Context for governance/risk
        previous_data_record = template_data_service.load_template_data(startup_id, template_key)
        previous_data = previous_data_record.get("data") if previous_data_record else None

        premise_service = ClientPremiseService(db)
        premise_result = premise_service.ensure_premise_or_fallback(startup_id)
        premises_payload = premise_result.get("premises")
        premises_status = premise_result.get("status")

        governance_engine = GovernanceEngine()
        gate_service = GovernanceGateService(db)
        risk_engine = RiskDetectionEngine()
        risk_signal_service = RiskSignalService(db)

        governance_results = []
        risk_result_dict: Optional[Dict[str, Any]] = None
        cognitive_signals: Optional[Dict[str, Any]] = None

        # Governance gates (observational by default)
        if config.method_governance or config.enable_governance_gates:
            gate = gate_service.latest_gate(template_key, vertical=None)
            if gate:
                gate_result = governance_engine.evaluate_gate(
                    gate,
                    template_key=template_key,
                    data=request.data,
                    previous_data=previous_data,
                )
                governance_results.append(gate_result.to_dict())
                if config.enable_governance_gates and gate_result.block_on_fail and not gate_result.passed:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={
                            "message": "Governance gate not satisfied",
                            "violations": [v.to_dict() for v in gate_result.violations],
                        },
                    )

        # Risk assessment (observational by default)
        if config.risk_engine or config.enable_risk_blocking:
            assessment = risk_engine.assess_template_response(
                template_key=template_key,
                data=request.data,
                previous_versions=[previous_data] if previous_data else None,
                related_templates=None,
                premises=premises_payload,
            )
            risk_result_dict = assessment.to_dict()

            # Persist risk signal
            risk_signal_service.record_signal(
                client_id=startup_id,
                template_key=template_key,
                risk_type="overall",
                severity=risk_result_dict.get("overall_risk", "low"),
                evidence=[f for f in risk_result_dict.get("red_flags", [])],
                violated_dependencies=[dep for flag in risk_result_dict.get("red_flags", []) for dep in (flag.get("violated_dependencies") or []) if isinstance(flag, dict)],
                recommendation="Revise itens com risco alto/crítico antes de avançar.",
                related_decisions=None,
            )

            if config.enable_risk_blocking and risk_result_dict.get("overall_risk") in {"high", "critical"}:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": "Risco elevado detectado",
                        "risk": risk_result_dict,
                    },
                )

            cognitive_signals = {
                "risk_level": risk_result_dict.get("overall_risk"),
                "strategic_alert": "Riscos detectados" if risk_result_dict.get("red_flags") else None,
                "violated_dependencies": [dep for flag in risk_result_dict.get("red_flags", []) for dep in (flag.get("violated_dependencies") or []) if isinstance(flag, dict)],
                "learning_feedback": "Revise as violações listadas para aumentar a confiança da decisão.",
            }

        # Save template data
        saved = template_data_service.save_template_data(
            startup_id=startup_id,
            template_key=template_key,
            data=request.data,
            auto_version=True
        )

        # Decision ledger (append-only) with governance/risk context
        ledger_service = DecisionLedgerService(db)
        ledger_service.record_decision(
            user_id=str(user.id),
            user_email=getattr(user, "email", ""),
            startup_id=startup_id,
            template_key=template_key,
            field_key="template_save",
            new_value=request.data,
            previous_value=previous_data,
            field_label=None,
            reasoning=None,
            source="founder",
            step_id=None,
            fcj_method_version="v1.0",
            cycle=None,
            related_template_snapshot=None,
            vertical=None,
            premises_used=[premises_payload] if premises_payload else None,
            ai_recommendation=None,
            risk_level=risk_result_dict.get("overall_risk") if risk_result_dict else None,
            human_confirmation=None,
            governance_result=governance_results if governance_results else None,
            risk_result=risk_result_dict,
        )

        # Audit log (if enabled)
        if config.ai_audit:
            try:
                audit_service = AIAuditService(db)
                audit_service.log_event(
                    user_id=str(user.id),
                    startup_id=startup_id,
                    event_type="decision_governance_risk",
                    model="n/a",
                    model_version=None,
                    prompt_hash=None,
                    prompt_version=None,
                    system_prompt_hash=None,
                    system_prompt_version=None,
                    input_tokens={"template_key": template_key},
                    tokens_used=None,
                    response_length=None,
                    latency_ms=None,
                    rules_version=str(governance_results[0].get("gate_version")) if governance_results else None,
                    validation_rules_applied=None,
                    governance_rules_active=[g.get("gate_id") for g in governance_results] if governance_results else None,
                    success=1,
                    error_message=None,
                    template_key=template_key,
                    context_snapshot={
                        "premises_status": premises_status,
                        "risk": risk_result_dict,
                        "governance": governance_results,
                    },
                )
            except Exception as audit_exc:
                logger.warning(f"Audit log skipped: {audit_exc}")

        logger.info(f"Saved template {template_key} v{saved['version']} for {startup_id}")

        return TemplateSavedDataResponse(**saved, cognitive_signals=cognitive_signals)

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
    db: Session = Depends(get_db),
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
        
        premise_service = ClientPremiseService(db)
        premise_result = premise_service.ensure_premise_or_fallback(startup_id)
        premises_payload = premise_result.get("premises")
        premises_status = premise_result.get("status")

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
            previous_templates=previous_templates,
            client_premises=premises_payload,
            premises_status=premises_status,
        )
        
        config = get_or_create_enterprise_config()
        if config.ai_audit:
            try:
                audit_service = AIAuditService(db)
                audit_service.log_event(
                    user_id=str(user.id),
                    startup_id=startup_id,
                    event_type="ai_mentor_payload",
                    model="n/a",
                    system_prompt_hash=None,
                    system_prompt_version=None,
                    input_tokens={"template_key": template_key, "premises_status": premises_status},
                    tokens_used=None,
                    response_length=None,
                    latency_ms=None,
                    rules_version=None,
                    validation_rules_applied=None,
                    success=1,
                    error_message=None,
                    template_key=template_key,
                    context_snapshot={
                        "premises_status": premises_status,
                        "premises_present": bool(premises_payload),
                        "current_field": current_field,
                    },
                )
            except Exception as audit_exc:
                logger.warning(f"Audit log skipped: {audit_exc}")

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
