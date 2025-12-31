"""
AI Mentor Context Generator & Prompts
=====================================

Generates intelligent payloads and system prompts for AI mentor chat integration.
Validates coherence between related templates and provides guided mentoring.

Features:
- Load related templates for context
- Build comprehensive mentor payload
- Validate data coherence across templates
- Generate template-specific system prompts
- Track field dependencies and recommendations
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Template hierarchy and relationships
TEMPLATE_RELATIONSHIPS = {
    "icp_01": {
        "name": "Ideal Customer Profile",
        "related_to": ["persona_01", "market_01"],
        "validation_rules": {
            "company_size": {"affects": ["persona_01.age_range", "persona_01.occupation"]},
            "industry": {"affects": ["persona_01.values", "persona_01.goals"]},
            "budget": {"affects": ["persona_01.pricing_sensitivity"]},
        },
    },
    "persona_01": {
        "name": "Customer Persona",
        "related_to": ["icp_01", "market_01", "value_prop_01"],
        "validation_rules": {
            "occupation": {"must_align_with": "icp_01.decision_making_style"},
            "goals": {"should_match": "value_prop_01.core_benefits"},
            "pain_points": {"should_relate_to": "icp_01.industry_challenges"},
        },
    },
    "market_01": {
        "name": "Market Analysis",
        "related_to": ["icp_01", "persona_01"],
        "validation_rules": {
            "location": {"affects": ["icp_01.geography", "persona_01.location"]},
            "market_size": {"should_relate_to": "icp_01.tam"},
        },
    },
    "value_prop_01": {
        "name": "Value Proposition",
        "related_to": ["persona_01", "icp_01"],
        "validation_rules": {
            "core_benefits": {
                "should_address": ["persona_01.pain_points", "persona_01.goals"]
            },
        },
    },
}


class AIMentorContextBuilder:
    """Builds context payloads for AI mentor."""

    def __init__(self, template_manager=None):
        self.template_manager = template_manager

    def get_related_templates(
        self, template_key: str, startup_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Load all related templates for coherence validation.

        For persona_01, loads icp_01 and market_01 if they exist.
        """
        related_data = {}

        if template_key not in TEMPLATE_RELATIONSHIPS:
            return related_data

        related_keys = TEMPLATE_RELATIONSHIPS[template_key].get("related_to", [])

        if not self.template_manager:
            return related_data

        for related_key in related_keys:
            try:
                data = self.template_manager.data_service.load_template_data(
                    startup_id, related_key
                )
                if data:
                    related_data[related_key] = data
            except Exception as e:
                logger.debug(f"Could not load related template {related_key}: {e}")

        return related_data

    def validate_coherence(
        self,
        template_key: str,
        current_data: Dict[str, Any],
        related_templates: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Validate data coherence across related templates.

        Returns list of issues/suggestions for the AI mentor to mention.
        """
        issues = []

        if template_key not in TEMPLATE_RELATIONSHIPS:
            return issues

        validation_rules = TEMPLATE_RELATIONSHIPS[template_key].get(
            "validation_rules", {}
        )

        # Check each rule
        for field, rule in validation_rules.items():
            if field not in current_data:
                continue

            field_value = current_data[field]

            # Check "must_align_with" rules
            if "must_align_with" in rule and related_templates:
                related_template, related_field = rule["must_align_with"].split(".")
                if related_template in related_templates:
                    related_value = related_templates[related_template].get("data", {}).get(
                        related_field
                    )
                    if related_value and field_value:
                        # Simple string similarity check
                        if not self._values_align(field_value, related_value):
                            issues.append(
                                {
                                    "type": "alignment_warning",
                                    "field": field,
                                    "message": f"'{field_value}' may not align with {related_template}.{related_field}: '{related_value}'",
                                    "severity": "warning",
                                }
                            )

            # Check "should_match" rules
            if "should_match" in rule and related_templates:
                related_template, related_field = rule["should_match"].split(".")
                if related_template in related_templates:
                    related_value = related_templates[related_template].get("data", {}).get(
                        related_field
                    )
                    if related_value and field_value:
                        if not self._values_similar(field_value, related_value):
                            issues.append(
                                {
                                    "type": "coherence_suggestion",
                                    "field": field,
                                    "message": f"Consider connecting this with {related_template}.{related_field}",
                                    "severity": "info",
                                }
                            )

        return issues

    @staticmethod
    def _values_align(value1: str, value2: str) -> bool:
        """Simple heuristic: check if values are semantically related."""
        # Normalize to lowercase and check for common keywords
        v1_lower = str(value1).lower()
        v2_lower = str(value2).lower()

        # Direct match or substring match
        if v1_lower in v2_lower or v2_lower in v1_lower:
            return True

        # Check for keyword overlap (at least 30% similarity)
        words1 = set(v1_lower.split())
        words2 = set(v2_lower.split())
        overlap = len(words1 & words2)
        total = len(words1 | words2)

        return overlap / total > 0.3 if total > 0 else False

    @staticmethod
    def _values_similar(value1: str, value2: str) -> bool:
        """Check if values are similar enough."""
        return AIMentorContextBuilder._values_align(value1, value2)


class AIMentorPromptGenerator:
    """Generate system prompts for AI mentor."""

    @staticmethod
    def generate_system_prompt(template_key: str, field_key: Optional[str] = None) -> str:
        """
        Generate system prompt for AI mentor based on template.

        If field_key is specified, focus on that specific field.
        """
        if template_key not in TEMPLATE_RELATIONSHIPS:
            return AIMentorPromptGenerator._generic_system_prompt()

        template_info = TEMPLATE_RELATIONSHIPS[template_key]
        template_name = template_info["name"]

        base_prompt = f"""You are an expert business advisor and mentor for the FCJ Venture Builder program.

The founder is currently filling out the "{template_name}" template as part of their startup planning process.

Your role is to:
1. **Guide their thinking** - Ask clarifying questions to deepen their understanding
2. **Validate coherence** - Check if their answers align with their overall business strategy
3. **Identify gaps** - Point out missing information or logical inconsistencies
4. **Provide suggestions** - Offer concrete examples and best practices based on their context
5. **Encourage specificity** - Push back on generic answers with "tell me more" questions

IMPORTANT RULES:
- NEVER respond generically - always reference their specific answers
- NEVER give lengthy advice - keep responses focused and actionable
- NEVER ask yes/no questions - ask open-ended questions that spark thinking
- ALWAYS validate against related templates (e.g., ICP, Market Analysis, Value Proposition)
- ALWAYS point out contradictions between fields in THIS template or across templates
- ALWAYS be encouraging but direct - FCJ founders appreciate honest feedback

Related templates they should have completed:
{chr(10).join(f"  • {TEMPLATE_RELATIONSHIPS[rel]['name']} ({rel})" for rel in template_info.get('related_to', []))}

Template structure they're filling:
- Has multiple sections (Identity, Psychographics, Behavior, Communication, etc.)
- Each field has a specific purpose in their go-to-market strategy
- Fields are interconnected - contradictions signal unclear thinking

When responding:
1. Always reference specific field names they just filled (show them you're reading their answers)
2. If you spot gaps or contradictions, flag them immediately with examples
3. If they mention pain points, always ask "how does your value prop solve this?"
4. If they mention goals, ask "what success looks like in 6 months?"
5. Before accepting their response as complete, ask one more probing question"""

        if field_key:
            field_prompt = AIMentorPromptGenerator._get_field_specific_prompt(
                template_key, field_key
            )
            return f"{base_prompt}\n\n---\n\nFOCUS ON THIS FIELD:\n{field_prompt}"

        return base_prompt

    @staticmethod
    def _get_field_specific_prompt(template_key: str, field_key: str) -> str:
        """Generate prompt focused on a specific field."""
        field_prompts = {
            # Persona fields
            "persona_name": """The persona name is their go-to-market targeting tool.

Ask questions like:
- "What makes this persona DIFFERENT from your other target segments?"
- "Would your sales team recognize this name in customer conversations?"
- "Does this name capture their aspirational identity or current state?"

Watch for: Generic names like "business owner" or "professional" - push for specificity""",

            "pain_points": """Pain points are the HOOK for your value proposition.

Ask questions like:
- "For each pain point, what's the business impact? (cost, time, revenue loss)"
- "How do they currently solve this today? What's broken about that?"
- "Which pain point creates the most urgency to change?"

Watch for: Vague pains like "lack of efficiency" - demand specific, measurable problems""",

            "goals": """Goals reveal what success looks like for this persona.

Ask questions like:
- "How would they measure achieving this goal? (KPIs)"
- "What timeline? (Are they urgent or patient?)"
- "Does this goal directly map to your value proposition?"

Watch for: Goals that don't align with pain points or your product offering""",

            "values": """Core values drive decision-making behavior.

Ask questions like:
- "When choosing vendors, how do these values show up?"
- "Would they sacrifice price for quality/speed/security? Why?"
- "Do your brand values align with theirs?"

Watch for: Values that contradict their other answers (e.g., "values security" but "early adopter of risky tech")""",

            "preferred_channels": """Communication channels determine your GTM mix.

Ask questions like:
- "Are they active or passive consumers? Do they seek info or wait for it?"
- "What channels show highest engagement? (Not just presence)"
- "Would they read a 20-page whitepaper or prefer a 2-min video?"

Watch for: Checking all channels equally - push them to prioritize""",

            "pricing_sensitivity": """Price sensitivity determines your monetization strategy.

Ask questions like:
- "What's their reference price? (What do they pay for similar solutions?)"
- "Is price their primary objection or just a factor?"
- "Would they pay premium for proven results?"

Watch for: Claiming "not price sensitive" while being "budget-conscious" - contradictions""",

            "role_in_buying": """Understanding their role reveals your sales process.

Ask questions like:
- "If they like your solution, can they make the decision alone?"
- "Who else needs to approve? (Finance, Security, Legal)"
- "How much power do they have to influence up/down?"

Watch for: Unclear on their actual influence - this matters for sales strategy""",

            "ideal_offer": """The ideal offer is where problem meets solution.

Ask questions like:
- "Is this what you're building, or are you building something different?"
- "What MUST be included vs. nice-to-have?"
- "How does this compare to current alternatives they're using?"

Watch for: Ideal offer that requires a different product than what you're building""",
        }

        return field_prompts.get(
            field_key,
            f"""This field is important for understanding your persona.

Consider:
- Is this answer specific and actionable?
- Does it connect to your value proposition?
- Would this insight change your go-to-market strategy?

Tell me more about what led you to this answer.""",
        )

    @staticmethod
    def _generic_system_prompt() -> str:
        """Fallback generic system prompt."""
        return """You are an expert business mentor for the FCJ Venture Builder program.

Help the founder think deeply about their answers by:
1. Asking clarifying questions
2. Pointing out gaps or contradictions
3. Validating that answers align across their business model
4. Providing specific, actionable guidance

Be direct but encouraging. Reference their specific answers, don't respond generically."""


class AIMentorPayloadBuilder:
    """Build complete payload for AI mentor chat."""

    def __init__(
        self,
        context_builder: Optional[AIMentorContextBuilder] = None,
        prompt_generator: Optional[AIMentorPromptGenerator] = None,
    ):
        self.context_builder = context_builder or AIMentorContextBuilder()
        self.prompt_generator = prompt_generator or AIMentorPromptGenerator()

    def build_payload(
        self,
        template_key: str,
        schema: Dict[str, Any],
        current_data: Dict[str, Any],
        current_field: Optional[str] = None,
        startup_id: Optional[str] = None,
        related_templates: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Build complete AI mentor payload."""
        # Validate coherence if we have related templates
        coherence_issues = []
        if related_templates:
            coherence_issues = self.context_builder.validate_coherence(
                template_key, current_data, related_templates
            )

        # Generate system prompt
        system_prompt = self.prompt_generator.generate_system_prompt(
            template_key, current_field
        )

        # Build field info
        fields_info = [
            {
                "key": f["key"],
                "label": f.get("label"),
                "type": f["type"],
                "section": f.get("section"),
                "value": current_data.get(f["key"]),
                "status": "filled"
                if current_data.get(f["key"])
                else "empty",
                "required": f.get("required", False),
            }
            for f in schema["fields"]
        ]

        return {
            "template_key": template_key,
            "template_name": schema.get("title", schema.get("sheet_name")),
            "current_field": current_field,
            "current_field_value": current_data.get(current_field)
            if current_field
            else None,
            "system_prompt": system_prompt,
            "template_data": current_data,
            "fields": fields_info,
            "coherence_issues": coherence_issues,
            "related_templates": related_templates or {},
            "timestamp": datetime.utcnow().isoformat(),
        }


# Example usage and exports
__all__ = [
    "AIMentorContextBuilder",
    "AIMentorPromptGenerator",
    "AIMentorPayloadBuilder",
    "TEMPLATE_RELATIONSHIPS",
]


def example_build_payload():
    """Example of building an AI mentor payload."""
    # This would be called from the FastAPI endpoint

    builder = AIMentorPayloadBuilder()

    schema = {
        "template_key": "persona_01",
        "title": "Customer Persona",
        "fields": [
            {"key": "persona_name", "label": "Persona Name", "type": "text"},
            {"key": "pain_points", "label": "Pain Points", "type": "textarea"},
            {"key": "goals", "label": "Goals", "type": "textarea"},
        ],
    }

    current_data = {
        "persona_name": "Young Urban Professional",
        "pain_points": "Time management, tool fragmentation, lack of visibility",
        "goals": "Streamline workflow, reduce context switching",
    }

    payload = builder.build_payload(
        template_key="persona_01",
        schema=schema,
        current_data=current_data,
        current_field="pain_points",
    )

    return payload


if __name__ == "__main__":
    import json

    payload = example_build_payload()
    print(json.dumps(payload, indent=2, default=str))
