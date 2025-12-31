"""
EXEMPLOS PRÁTICOS - Template Engine
====================================

Demonstra como usar cada componente do sistema em cenários reais.
"""

# ============================================================================
# EXEMPLO 1: Gerar Schema de um Template Excel
# ============================================================================

# Cenário: Novos templates foram adicionados a Template Q1.xlsx
# Tarefa: Gerar schemas JSON para renderização no frontend

from services.excel_template_parser import ExcelTemplateParser

def generate_all_template_schemas():
    """Generate schemas for all 26 FCJ templates."""
    
    parser = ExcelTemplateParser("data/excel_templates/Template Q1.xlsx")
    
    templates = [
        {
            "sheet_name": "Persona",
            "template_key": "persona_01",
            "title": "Customer Persona",
            "fields": {
                "persona_name": {"cell": "B2", "type": "text", "label": "Persona Name", "required": True},
                "age_range": {"cell": "B3", "type": "text", "label": "Age Range", "required": True},
                "occupation": {"cell": "B4", "type": "text", "label": "Occupation", "required": True},
                "values": {"cell": "B6", "type": "textarea", "label": "Core Values", "required": True},
                "pain_points": {"cell": "B7", "type": "textarea", "label": "Pain Points", "required": True},
                "goals": {"cell": "B8", "type": "textarea", "label": "Goals", "required": True},
                # ... 20+ more fields
            }
        },
        {
            "sheet_name": "ICP",
            "template_key": "icp_01",
            "title": "Ideal Customer Profile",
            "fields": {
                "company_name": {"cell": "B2", "type": "text", "label": "Company Name"},
                "industry": {"cell": "B3", "type": "text", "label": "Industry"},
                "company_size": {"cell": "B4", "type": "enum", "label": "Company Size", 
                               "validation_rules": {"enum": ["1-10", "11-50", "51-200", "200+"]}},
                # ... more fields
            }
        },
        # ... 24 more templates
    ]
    
    for template_config in templates:
        schema = parser.parse_sheet(
            sheet_name=template_config["sheet_name"],
            fields=template_config["fields"],
            template_key=template_config["template_key"],
            title=template_config["title"]
        )
        
        parser.export_schema_to_json(
            schema,
            f"data/schemas/{schema.template_key}.json"
        )
        
        print(f"✅ Generated: {template_config['template_key']}.json")
    
    parser.close()
    print(f"\n✅ All {len(templates)} schemas generated successfully!")


# ============================================================================
# EXEMPLO 2: Founder Preenchendo Template no Frontend
# ============================================================================

# Cenário: Founder "João da Silva" está preenchendo Persona
# Fluxo completo: carregar → preencher → salvar → exportar

from services.template_manager import TemplateManager

def founder_workflow_example():
    """Demonstrates complete founder workflow."""
    
    # Step 1: Founder acessa /founder/templates/persona_01
    # Frontend faz GET request para carregar schema
    
    manager = TemplateManager()
    startup_id = "startup_uuid_joao_silva"
    template_key = "persona_01"
    
    # Backend retorna template completo
    template = manager.get_template_for_founder(startup_id, template_key)
    print(f"Loaded template: {template['schema']['title']}")
    print(f"Fields: {len(template['schema']['fields'])}")
    print(f"Previous save (v{template['saved_data']['version']}): {template['saved_data']['data']}")
    
    # Step 2: Founder preenche formulário
    founder_response = {
        "persona_name": "Gerente de Startup Tech",
        "age_range": "30-40",
        "gender": "Male",
        "occupation": "Startup Manager",
        "income_range": "$80,000 - $150,000",
        "education": "Master's",
        "location": "São Paulo, Brazil",
        
        "values": "Innovation, Speed, Autonomy, Growth",
        "pain_points": "Lack of visibility into company metrics, Manual processes taking 30% of time, "
                      "Difficulty hiring technical talent, Cash burn rate unpredictability",
        "goals": "Scale to 50 employees, Achieve product-market fit, Raise Series A in 2025",
        "fears_objections": "Market saturation, Unable to compete with well-funded competitors, "
                           "Losing key team members",
        
        "preferred_channels": "LinkedIn for news, Twitter for trends, Direct email for important updates, "
                             "Slack for real-time communication",
        "content_preferences": "Case studies, Product demos, 15-min YouTube videos, Podcast episodes",
        "social_media": "LinkedIn (very active), Twitter (daily), GitHub (occasional)",
        
        "technology_adoption": "Early Adopter",
        "decision_making_style": "Fast & Decisive",
        "buying_triggers": "When current tool breaks or slows down team, Quarterly budget review cycles",
        "budget_availability": "Limited",
        "success_metrics": "Time saved per week, Cost reduction, Team satisfaction score",
        "timeline_urgency": "Short-term (1-4 weeks)",
        
        "personal_interests": "Rock climbing, Cooking, Startup podcasts, Sci-fi books",
        "industry_expertise": "10 years in tech, 5 years in startups, 1 year as founder",
        "role_in_buying": "Decision Maker",
        "influence_factors": "Peer recommendations, Data/ROI analysis, Free trial availability",
        "brand_perception": "Values quality over brand name, Open to switching if better solution",
        "pricing_sensitivity": "Price conscious",
        "motivation_drivers": "Achievement, autonomy, making an impact",
        "objection_overcoming": "Case studies with similar startups, Free 30-day trial, Money-back guarantee",
        
        "ideal_offer": "SaaS platform with integrated metrics dashboard, Slack notifications, "
                      "1-click expense tracking, $99-199/month pricing"
    }
    
    # Step 3: Frontend valida localmente, depois salva no backend
    validation = manager.data_service.validate_data(template_key, founder_response)
    
    if not validation["valid"]:
        print(f"❌ Validation errors:")
        for error in validation["errors"]:
            print(f"  - {error['field']}: {error['message']}")
        return
    
    # Step 4: Salvar no backend
    saved = manager.save_founder_response(
        startup_id=startup_id,
        template_key=template_key,
        data=founder_response
    )
    
    print(f"\n✅ Saved! Version: {saved['version']}")
    print(f"Updated at: {saved['updated_at']}")
    
    # Step 5: Founder clica "Export to Excel"
    excel_path = manager.export_founder_template(
        startup_id=startup_id,
        template_key=template_key,
        original_excel_path="data/excel_templates/Template Q1.xlsx",
        output_dir="exports"
    )
    
    print(f"✅ Exported to: {excel_path}")
    return saved


# ============================================================================
# EXEMPLO 3: AI Mentor Validando Coerência
# ============================================================================

# Cenário: Founder preencheu Persona e ICP
# AI Mentor verifica se são coerentes

from services.ai_mentor_context import AIMentorContextBuilder, AIMentorPayloadBuilder

def ai_mentor_coherence_check():
    """Check coherence between related templates."""
    
    startup_id = "startup_uuid_joao_silva"
    
    # Founder data for both templates
    persona_data = {
        "persona_name": "Gerente de Startup Tech",
        "occupation": "Startup Manager",
        "age_range": "30-40",
        "goals": "Scale to 50 employees, achieve Series A",
        "pain_points": "Lack of visibility, manual processes",
        "pricing_sensitivity": "Price conscious",
    }
    
    icp_data = {
        "company_size": "1-10",  # Early stage
        "industry": "B2B SaaS",
        "decision_making_style": "Consensus-driven",  # ⚠️ CONTRADICTION
        "budget": "Limited",
    }
    
    # Load schema
    from services.template_manager import TemplateDataService
    service = TemplateDataService()
    persona_schema = service.load_schema("persona_01")
    
    # Check coherence
    context_builder = AIMentorContextBuilder()
    
    issues = context_builder.validate_coherence(
        template_key="persona_01",
        current_data=persona_data,
        related_templates={"icp_01": {"data": icp_data}}
    )
    
    if issues:
        print("⚠️ Coherence Issues Found:\n")
        for issue in issues:
            print(f"  [{issue['severity'].upper()}] {issue['field']}")
            print(f"  {issue['message']}\n")
    else:
        print("✅ All templates are coherent!")
    
    # Generate AI mentor payload with smart prompts
    payload_builder = AIMentorPayloadBuilder(context_builder)
    
    payload = payload_builder.build_payload(
        template_key="persona_01",
        schema=persona_schema.to_dict(),
        current_data=persona_data,
        current_field="goals",
        startup_id=startup_id,
        related_templates={"icp_01": {"data": icp_data}}
    )
    
    print("\n📋 AI Mentor Payload:")
    print(f"Field: {payload['current_field']}")
    print(f"Value: {payload['current_field_value']}")
    print(f"\nCoherence issues to address: {len(payload['coherence_issues'])}")
    
    return payload


# ============================================================================
# EXEMPLO 4: Integração com Chat API
# ============================================================================

# Cenário: Founder clica ✨ para perguntar ao AI Mentor
# Sistema envia contexto completo para chat

async def send_to_ai_mentor_chat(mentor_payload, user_message: str):
    """Send founder's question to AI mentor with full context."""
    
    import json
    import httpx
    
    # Prepare full context
    chat_context = {
        "template": {
            "key": mentor_payload["template_key"],
            "name": mentor_payload["template_name"],
            "current_field": mentor_payload["current_field"],
        },
        "founder_data": mentor_payload["template_data"],
        "field_info": {
            f["key"]: {
                "label": f["label"],
                "value": f.get("value"),
                "status": f.get("status")
            }
            for f in mentor_payload.get("fields", [])
        },
        "coherence_issues": mentor_payload.get("coherence_issues", []),
        "related_templates": {
            k: v.get("data", {})
            for k, v in mentor_payload.get("related_templates", {}).items()
        }
    }
    
    # Send to chat API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={
                "template_context": chat_context,
                "system_prompt": mentor_payload["system_prompt"],
                "user_message": user_message
            }
        )
        
        chat_response = response.json()
        return chat_response


# ============================================================================
# EXEMPLO 5: Versionamento e Histórico
# ============================================================================

# Cenário: Founder quer ver histórico de mudanças

def show_template_history():
    """Display version history of a template."""
    
    from services.template_manager import TemplateDataService
    
    service = TemplateDataService()
    startup_id = "startup_uuid_joao_silva"
    template_key = "persona_01"
    
    versions = service.list_template_versions(startup_id, template_key)
    
    print(f"📚 Version History for {template_key}\n")
    print("Version | Updated | Fields Changed")
    print("--------|---------|----------------")
    
    for i, version_data in enumerate(versions, 1):
        print(f"  v{version_data['version']}    | {version_data['updated_at'][:10]} | "
              f"{len(version_data['data'])} fields filled")
    
    # Compare two versions
    if len(versions) >= 2:
        v1_data = versions[-2]["data"]
        v2_data = versions[-1]["data"]
        
        changed = {k: (v1_data.get(k), v2_data.get(k)) 
                  for k in v2_data if v1_data.get(k) != v2_data.get(k)}
        
        print(f"\n🔄 Changes in v{versions[-1]['version']}:")
        for field, (old, new) in changed.items():
            print(f"  • {field}: '{old}' → '{new}'")


# ============================================================================
# EXEMPLO 6: Gerando Imagens de Fundo
# ============================================================================

# Cenário: Precisamos gerar screenshots dos templates para o frontend

def generate_template_background_images():
    """Generate PNG background images for all templates."""
    
    from PIL import Image, ImageDraw, ImageFont
    import json
    from pathlib import Path
    
    schemas_dir = Path("data/schemas")
    output_dir = Path("frontend/public/images/templates")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for schema_file in schemas_dir.glob("*.json"):
        with open(schema_file) as f:
            schema = json.load(f)
        
        # Create image
        width = int(schema["sheet_width"])
        height = int(schema["sheet_height"])
        
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        
        # Draw header
        draw.rectangle([0, 0, width, 50], fill="#0066cc")
        draw.text((20, 15), schema["title"], fill="white")
        
        # Draw fields as boxes
        for field in schema["fields"]:
            pos = field["position"]
            x1, y1 = int(pos["left"]), int(pos["top"])
            x2, y2 = x1 + int(pos["width"]), y1 + int(pos["height"])
            
            # Draw cell border
            draw.rectangle([x1, y1, x2, y2], outline="#cccccc")
            
            # Draw label
            if y1 > 50:  # Skip header area
                draw.text((x1 + 5, y1 + 2), field["label"], fill="#666666")
        
        # Save
        output_path = output_dir / f"{schema['template_key']}.png"
        img.save(output_path)
        print(f"✅ Generated: {output_path}")


# ============================================================================
# EXEMPLO 7: Batch Import de Templates Existentes
# ============================================================================

# Cenário: Empresa tem múltiplos startups já preenchidos
# Desejam importar dados históricos

def import_existing_templates():
    """Import previously filled templates into the system."""
    
    from services.template_manager import TemplateManager
    import json
    
    manager = TemplateManager()
    
    # Dados históricos em CSV/JSON
    historical_data = [
        {
            "startup_id": "startup_001",
            "template_key": "persona_01",
            "data": {
                "persona_name": "Early Adopter Dev",
                "age_range": "25-30",
                "occupation": "Software Developer"
            }
        },
        {
            "startup_id": "startup_002",
            "template_key": "persona_01",
            "data": {
                "persona_name": "Product Manager",
                "age_range": "35-45",
                "occupation": "Product Manager"
            }
        },
    ]
    
    for entry in historical_data:
        saved = manager.save_founder_response(
            startup_id=entry["startup_id"],
            template_key=entry["template_key"],
            data=entry["data"]
        )
        print(f"✅ Imported: {entry['startup_id']}/{entry['template_key']}")


# ============================================================================
# EXEMPLO 8: Reporting e Analytics
# ============================================================================

# Cenário: Analisar progresso de startups no preenchimento de templates

def template_completion_analytics():
    """Analyze template completion rates across all startups."""
    
    from pathlib import Path
    import json
    
    templates_dir = Path("data/templates")
    
    stats = {
        "total_startups": 0,
        "total_templates_filled": 0,
        "templates_by_startup": {},
        "average_versions_per_template": 0,
    }
    
    for startup_dir in templates_dir.iterdir():
        if startup_dir.is_dir():
            startup_id = startup_dir.name
            template_count = 0
            version_counts = []
            
            for template_dir in startup_dir.iterdir():
                if template_dir.is_dir():
                    versions = list(template_dir.glob("v*.json"))
                    if versions:
                        template_count += 1
                        version_counts.append(len(versions))
            
            if template_count > 0:
                stats["total_startups"] += 1
                stats["total_templates_filled"] += template_count
                stats["templates_by_startup"][startup_id] = {
                    "filled": template_count,
                    "avg_versions": sum(version_counts) / len(version_counts)
                }
    
    print("📊 Template Completion Analytics\n")
    print(f"Total startups: {stats['total_startups']}")
    print(f"Total templates filled: {stats['total_templates_filled']}")
    print(f"Average templates per startup: {stats['total_templates_filled'] / stats['total_startups']:.1f}")
    
    return stats


# ============================================================================
# MAIN: Run Examples
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    print("=" * 60)
    print("EXEMPLOS PRÁTICOS - Template Engine TR4CTION v2")
    print("=" * 60)
    
    # Example 1
    # print("\n[1] Generating schemas...")
    # generate_all_template_schemas()
    
    # Example 2
    print("\n[2] Founder workflow...")
    founder_response = founder_workflow_example()
    
    # Example 3
    print("\n[3] AI Mentor coherence check...")
    mentor_payload = ai_mentor_coherence_check()
    
    # Example 4
    # print("\n[4] Sending to AI mentor...")
    # asyncio.run(send_to_ai_mentor_chat(mentor_payload, "Are my goals realistic?"))
    
    # Example 5
    # print("\n[5] Template history...")
    # show_template_history()
    
    # Example 7
    # print("\n[7] Importing existing templates...")
    # import_existing_templates()
    
    # Example 8
    # print("\n[8] Analytics...")
    # template_completion_analytics()
