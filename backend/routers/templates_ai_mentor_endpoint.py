"""
AI Mentor Integration
====================
Update to templates router to integrate AI mentor with template context.

Add this to routers/templates.py
"""

# Add to imports
from services.ai_mentor_context import (
    AIMentorContextBuilder,
    AIMentorPayloadBuilder,
    AIMentorPromptGenerator,
)

# Add these instances after the existing service initialization
ai_context_builder = AIMentorContextBuilder(template_manager)
ai_mentor_builder = AIMentorPayloadBuilder()

# ============================================================================
# NEW ENDPOINT: Enhanced AI Mentor with Full Context
# ============================================================================


class AIMentorFullPayload(BaseModel):
    """Complete payload for AI mentor with all context."""

    template_key: str
    template_name: str
    current_field: Optional[str] = None
    current_field_label: Optional[str] = None
    current_field_value: Optional[Any] = None
    system_prompt: str
    template_data: Dict[str, Any]
    fields: list[Dict[str, Any]]
    coherence_issues: list[Dict[str, Any]] = []
    related_templates: Dict[str, Any] = {}


@router.post(
    "/{template_key}/ai-mentor/full",
    response_model=AIMentorFullPayload,
    summary="Get Full AI Mentor Context",
    description="Get complete context including related templates and coherence validation",
)
async def get_ai_mentor_full_context(
    template_key: str,
    current_field: Optional[str] = None,
    startup_id: str = Depends(get_user_startup_id),
    user: User = Depends(get_current_founder),
):
    """
    Get complete AI mentor payload with:
    - Current template data
    - Related templates for coherence checking
    - Custom system prompt based on template type
    - Coherence validation issues/suggestions
    - Specific guidance if field is specified
    """
    try:
        # Load current template
        schema = template_data_service.load_schema(template_key)
        saved_data = template_data_service.load_template_data(startup_id, template_key)
        current_data = saved_data.get("data", {}) if saved_data else {}

        # Load related templates
        related_templates = ai_context_builder.get_related_templates(
            template_key, startup_id
        )

        # Get field label if specified
        field_label = None
        if current_field:
            field = next((f for f in schema.fields if f.key == current_field), None)
            if field:
                field_label = field.label

        # Build full payload
        payload = ai_mentor_builder.build_payload(
            template_key=template_key,
            schema=schema.to_dict(),
            current_data=current_data,
            current_field=current_field,
            startup_id=startup_id,
            related_templates=related_templates,
        )

        return AIMentorFullPayload(
            template_key=payload["template_key"],
            template_name=payload["template_name"],
            current_field=payload["current_field"],
            current_field_label=field_label,
            current_field_value=payload["current_field_value"],
            system_prompt=payload["system_prompt"],
            template_data=payload["template_data"],
            fields=payload["fields"],
            coherence_issues=payload["coherence_issues"],
            related_templates=payload["related_templates"],
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_key}' not found",
        )
    except Exception as e:
        logger.error(f"Error building AI mentor context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================================
# EXISTING ENDPOINT: Simplified AI Mentor (keep for backward compatibility)
# ============================================================================

# The existing endpoint in templates.py remains but can be updated to call the full version


@router.post(
    "/{template_key}/ai-mentor",
    response_model=AIMentorPayload,
    summary="Prepare AI Mentor Payload (Simplified)",
    description="Prepare template context for AI mentor chat (simplified version)",
)
async def prepare_ai_mentor_payload_simplified(
    template_key: str,
    current_field: Optional[str] = None,
    startup_id: str = Depends(get_user_startup_id),
    user: User = Depends(get_current_founder),
):
    """
    Simplified version that calls the full context endpoint.
    For backward compatibility.
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

        # Load related templates
        related_templates = ai_context_builder.get_related_templates(
            template_key, startup_id
        )

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
            previous_templates=related_templates if related_templates else None,
        )

        logger.info(f"Prepared AI mentor payload for {template_key}")

        return payload

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_key}' not found",
        )
    except Exception as e:
        logger.error(f"Error preparing AI mentor payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
