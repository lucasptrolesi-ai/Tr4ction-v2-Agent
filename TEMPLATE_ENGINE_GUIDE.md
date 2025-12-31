# 🎯 Excel Template Engine - Complete Implementation Guide

**Project**: TR4CTION v2 Agent - FCJ Venture Builder  
**Component**: Excel-to-Web Template Rendering Engine  
**Status**: Production-Ready  
**Last Updated**: 2025-01-01

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Backend Setup](#backend-setup)
3. [Frontend Integration](#frontend-integration)
4. [Template Configuration](#template-configuration)
5. [AI Mentor Integration](#ai-mentor-integration)
6. [API Reference](#api-reference)
7. [Deployment Checklist](#deployment-checklist)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

### System Flow

```
Excel Template (Template Q1.xlsx)
    ↓
[Python Parser] → Calculates exact pixel positions → JSON Schema
    ↓
[FastAPI Backend] → Serves schema + manages persistence
    ↓
[React Frontend] → Renders canvas with overlay inputs
    ↓
[AI Mentor] → Validates coherence + guides founder
    ↓
[Export] → Returns filled Excel to founder
```

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Excel Parser** | openpyxl, Python | Converts Excel → pixel positions |
| **Template Service** | FastAPI, Python | CRUD + persistence + export |
| **Backend Routes** | FastAPI | REST endpoints for founders |
| **Frontend Component** | React/Next.js | Canvas rendering + form inputs |
| **AI Mentor** | Python service | Context builder + prompt generation |

### Design Principles

✅ **Fidelity First**: Excel layout is pixel-perfect in web  
✅ **No Hardcoding**: All positions calculated from Excel dimensions  
✅ **Scalable**: Works for all 26 FCJ templates  
✅ **Composable**: Reusable services and components  
✅ **Data Persistence**: Auto-versioning of founder responses  
✅ **Intelligent Mentoring**: Context-aware guidance based on template relations  

---

## 🔧 Backend Setup

### Installation

```bash
# Install dependencies
cd backend
pip install openpyxl fastapi pydantic

# Create necessary directories
mkdir -p data/schemas
mkdir -p data/templates
mkdir -p data/excel_templates
mkdir -p exports
```

### 1. Configure Excel Template Metadata

Create template configuration file for each sheet:

```python
# backend/config/templates.py

TEMPLATE_CONFIGS = {
    "persona_01": {
        "excel_path": "data/excel_templates/Template Q1.xlsx",
        "sheet_name": "Persona",
        "output_sheet_name": "Persona",  # Where to write responses
    },
    "icp_01": {
        "excel_path": "data/excel_templates/Template Q1.xlsx",
        "sheet_name": "ICP",
    },
    # ... other 24 templates
}
```

### 2. Generate Schema from Excel

```python
# backend/scripts/generate_schemas.py

from services.excel_template_parser import ExcelTemplateParser

parser = ExcelTemplateParser("data/excel_templates/Template Q1.xlsx")

# Define editable fields for each sheet
persona_fields = {
    "persona_name": {
        "cell": "B2",
        "type": "text",
        "label": "Persona Name",
        "required": True,
        "section": "Identity",
        "help_text": "Give this persona a memorable name...",
    },
    # ... all other fields
}

# Generate schema
schema = parser.parse_sheet(
    sheet_name="Persona",
    fields=persona_fields,
    template_key="persona_01",
    title="Customer Persona Template"
)

# Save schema
parser.export_schema_to_json(
    schema,
    "data/schemas/persona_01.json"
)
```

Run this script to generate all schemas:

```bash
python backend/scripts/generate_schemas.py
```

### 3. Register Router in main.py

```python
# backend/main.py

from routers.templates import router as templates_router

app.include_router(
    templates_router,
    prefix="/api/founder",
    tags=["templates"]
)
```

### 4. Verify Setup

```bash
# Check if schemas are loaded
curl http://localhost:8000/api/founder/templates/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "template-manager",
#   "schemas_available": 26
# }
```

---

## 🎨 Frontend Integration

### 1. Install React Component

The `TemplateCanvas` component is located at:  
`frontend/components/TemplateCanvas.jsx`

This component:
- Renders background image of Excel sheet
- Positions inputs absolutely using pixel values
- Handles validation and auto-save
- Integrates with AI mentor

### 2. Create Template Page

```jsx
// frontend/app/founder/templates/[templateId]/page.jsx

'use client';

import TemplateCanvas from '@/components/TemplateCanvas';
import { useState, useEffect } from 'react';

export default function TemplatePage() {
  const [schema, setSchema] = useState(null);
  const [backgroundImage, setBackgroundImage] = useState(null);
  
  useEffect(() => {
    // Load template schema
    fetch(`/api/founder/templates/${templateId}`)
      .then(r => r.json())
      .then(data => {
        setSchema(data.schema);
        // Load background image (pre-generated Excel screenshot)
        setBackgroundImage(`/images/templates/${templateId}.png`);
      });
  }, [templateId]);
  
  const handleSave = async (data) => {
    await fetch(`/api/founder/templates/${templateId}`, {
      method: 'POST',
      body: JSON.stringify({ data })
    });
  };
  
  return (
    <TemplateCanvas
      schema={schema}
      backgroundImage={backgroundImage}
      onSave={handleSave}
    />
  );
}
```

### 3. Generate Background Images

For pixel-perfect fidelity, generate screenshots of each Excel template:

```python
# backend/scripts/generate_template_images.py

from openpyxl.drawing.image import Image as XLImage
from openpyxl.worksheet.worksheet import Worksheet
import subprocess

def generate_template_screenshots():
    """
    Generate PNG screenshots of each Excel template.
    
    Options:
    1. LibreOffice headless conversion
    2. Excel COM (Windows only)
    3. Custom rendering using Pillow
    """
    
    # Option 1: LibreOffice command-line
    templates = [
        ("data/excel_templates/Template Q1.xlsx", "Persona", "persona_01"),
        # ... other sheets
    ]
    
    for excel_path, sheet_name, template_key in templates:
        # Convert sheet to PDF first
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            excel_path
        ])
        
        # Convert PDF page to PNG
        subprocess.run([
            "convert", f"{excel_path.replace('.xlsx', '.pdf')}",
            f"frontend/public/images/templates/{template_key}.png"
        ])

if __name__ == "__main__":
    generate_template_screenshots()
```

Or use a simpler approach with Pillow:

```python
# Generate placeholder backgrounds on-the-fly
def generate_placeholder_image(schema):
    """Generate a simple grid-based placeholder."""
    from PIL import Image, ImageDraw
    
    img = Image.new(
        'RGB',
        (int(schema['sheet_width']), int(schema['sheet_height'])),
        'white'
    )
    draw = ImageDraw.Draw(img)
    
    # Draw grid
    for field in schema['fields']:
        pos = field['position']
        draw.rectangle(
            [pos['left'], pos['top'], 
             pos['left'] + pos['width'], 
             pos['top'] + pos['height']],
            outline='gray'
        )
        draw.text(
            (pos['left'] + 5, pos['top'] + 5),
            field['label'],
            fill='gray'
        )
    
    img.save(f"frontend/public/images/templates/{schema['template_key']}.png")
```

### 4. API Client Setup

```javascript
// frontend/lib/api.js

export async function apiCall(endpoint, options = {}) {
  const token = localStorage.getItem('auth_token');
  
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}${endpoint}`,
    {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    }
  );
  
  return response;
}
```

---

## 📝 Template Configuration

### Creating a New Template Schema

1. **Open Excel file** in `data/excel_templates/Template Q1.xlsx`

2. **Identify sheet and fields** you want to make editable

3. **Run parser** to calculate positions:

```python
from services.excel_template_parser import ExcelTemplateParser

parser = ExcelTemplateParser("Template Q1.xlsx")

fields = {
    "field_key_1": {
        "cell": "B2",
        "type": "text",  # text, textarea, number, date, enum, etc.
        "label": "Human Readable Label",
        "required": True,
        "section": "Section Name",
        "validation_rules": {
            "min": 5,
            "max": 100,
            "pattern": "^[A-Z]"
        }
    },
    # ... more fields
}

schema = parser.parse_sheet(
    sheet_name="SheetName",
    fields=fields,
    template_key="template_key_unique"
)

parser.export_schema_to_json(schema, f"data/schemas/{schema.template_key}.json")
```

4. **Verify schema** in `data/schemas/template_key.json`

### Field Types Supported

| Type | Usage | HTML Input |
|------|-------|-----------|
| `text` | Short text (name, title) | `<input type="text">` |
| `textarea` | Multi-line text (description) | `<textarea>` |
| `email` | Email addresses | `<input type="email">` |
| `phone` | Phone numbers | `<input type="tel">` |
| `url` | Website URLs | `<input type="url">` |
| `number` | Whole numbers | `<input type="number">` |
| `decimal` | Decimals | `<input type="number" step="0.01">` |
| `currency` | Money amounts | `<input type="number" step="0.01">` |
| `percentage` | Percentages | `<input type="number">` |
| `date` | Calendar dates | `<input type="date">` |
| `boolean` | Yes/no checkbox | `<input type="checkbox">` |
| `enum` | Dropdown selection | `<select><option>` |

### Validation Rules

```json
{
  "field_key": {
    "type": "text",
    "validation_rules": {
      "min": 3,
      "max": 100,
      "pattern": "^[A-Za-z0-9\\s-]+$",
      "enum": ["Option1", "Option2"],
      "required": true
    }
  }
}
```

---

## 🧠 AI Mentor Integration

### How It Works

1. Founder fills template field
2. Clicks "✨ AI Mentor" button
3. System loads:
   - Current template data
   - Related templates (for coherence validation)
   - Field-specific prompts
   - Coherence issues/suggestions
4. AI mentor chat opens with smart guidance

### Template Relations

```python
TEMPLATE_RELATIONSHIPS = {
    "icp_01": {
        "name": "Ideal Customer Profile",
        "related_to": ["persona_01", "market_01"],
    },
    "persona_01": {
        "name": "Customer Persona",
        "related_to": ["icp_01", "market_01", "value_prop_01"],
    },
    # ... etc
}
```

### Coherence Validation

AI mentor checks:
- Does persona occupation match ICP decision-making style?
- Do persona pain points relate to ICP industry challenges?
- Do goals align with value proposition benefits?
- Any contradictions within the template?

### System Prompt Generation

Prompts are dynamically generated based on:
- Current template context
- Specific field being edited
- Related templates data
- Coherence issues found

Example prompt focus for "pain_points" field:

```
Pain points are the HOOK for your value proposition.

Ask questions like:
- "For each pain point, what's the business impact? (cost, time, revenue loss)"
- "How do they currently solve this today? What's broken about that?"
- "Which pain point creates the most urgency to change?"

Watch for: Vague pains like "lack of efficiency" - demand specific problems
```

---

## 🔌 API Reference

### Get Template

```bash
GET /api/founder/templates/{template_key}
Authorization: Bearer {token}

Response:
{
  "schema": { ... },
  "saved_data": {
    "template_key": "persona_01",
    "startup_id": "uuid",
    "data": { "field_key": "value", ... },
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00",
    "version": 3
  },
  "versions": [ ... ]
}
```

### Save Template Response

```bash
POST /api/founder/templates/{template_key}
Authorization: Bearer {token}
Content-Type: application/json

Request Body:
{
  "data": {
    "persona_name": "Young Urban Professional",
    "age_range": "25-35",
    "occupation": "Software Engineer",
    ...
  }
}

Response:
{
  "template_key": "persona_01",
  "startup_id": "uuid",
  "data": { ... },
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:35:00",
  "version": 4
}
```

### Export to Excel

```bash
POST /api/founder/templates/{template_key}/export
Authorization: Bearer {token}

Response:
{
  "message": "Export successful",
  "file_url": "/api/downloads/uuid_persona_01_20240115_103000.xlsx",
  "startup_id": "uuid",
  "template_key": "persona_01"
}
```

### List Versions

```bash
GET /api/founder/templates/{template_key}/versions
Authorization: Bearer {token}

Response:
[
  {
    "template_key": "persona_01",
    "version": 1,
    "data": { ... },
    "created_at": "2024-01-15T10:30:00"
  },
  { ... more versions ... }
]
```

### AI Mentor Context

```bash
POST /api/founder/templates/{template_key}/ai-mentor/full?current_field=pain_points
Authorization: Bearer {token}

Response:
{
  "template_key": "persona_01",
  "template_name": "Customer Persona",
  "current_field": "pain_points",
  "current_field_label": "Main Pain Points",
  "system_prompt": "Pain points are the HOOK...",
  "template_data": { ... },
  "fields": [ ... ],
  "coherence_issues": [
    {
      "type": "alignment_warning",
      "field": "goals",
      "message": "Goals may not align with icp_01.decision_making_style",
      "severity": "warning"
    }
  ],
  "related_templates": {
    "icp_01": { "data": { ... } }
  }
}
```

---

## ✅ Deployment Checklist

### Pre-Deployment

- [ ] All 26 template schemas generated and validated
- [ ] Background images generated for each template
- [ ] Excel export tested end-to-end
- [ ] AI mentor prompts reviewed for accuracy
- [ ] Database migration for template data persistence
- [ ] Environment variables configured

### Database Schema

```sql
-- Template data persistence table
CREATE TABLE template_responses (
  id UUID PRIMARY KEY,
  startup_id UUID NOT NULL,
  template_key VARCHAR(50) NOT NULL,
  data JSONB NOT NULL,
  version INT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(startup_id, template_key, version)
);

-- Index for quick lookups
CREATE INDEX idx_template_startup ON template_responses(startup_id, template_key);
```

### Environment Variables

```bash
# backend/.env
TEMPLATE_DATA_DIR=data/templates
TEMPLATE_SCHEMAS_DIR=data/schemas
EXCEL_TEMPLATES_DIR=data/excel_templates
EXPORT_DIR=exports

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Docker Deployment

```dockerfile
# backend/Dockerfile additions
COPY data/schemas /app/data/schemas
COPY data/excel_templates /app/data/excel_templates
RUN mkdir -p /app/data/templates /app/exports
```

### Monitoring

Track:
- Template completion rates per founder
- Average time per template
- Export success/failure rates
- AI mentor engagement (% clicking ✨)

---

## 🐛 Troubleshooting

### Issue: Inputs not aligning with cells

**Cause**: Zoom level or DPI mismatch

**Solution**:
```javascript
// TemplateCanvas.jsx - adjust scale calculation
const pixelScale = (containerWidth / schema.sheet_width) * window.devicePixelRatio;
```

### Issue: Excel export has wrong values

**Cause**: Cell address mismatch in schema

**Solution**:
```python
# Verify cell addresses in schema
for field in schema.fields:
    cell = worksheet[field.cell]
    print(f"{field.key} → {field.cell} = {cell.value}")
```

### Issue: AI mentor not loading

**Cause**: Related templates not found or service error

**Solution**:
```bash
# Check if schemas exist
ls data/schemas/

# Test endpoint
curl http://localhost:8000/api/founder/templates/persona_01/ai-mentor/full
```

### Issue: Validation errors not shown

**Cause**: Frontend not displaying validation response

**Solution**:
```javascript
// Check browser console for validation errors
const validation = await apiCall(url, {method: 'POST', body});
if (!validation.ok) {
  const err = await validation.json();
  console.error('Validation:', err.detail);
}
```

---

## 📚 References

- [openpyxl Documentation](https://openpyxl.readthedocs.io/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Excel Position Calculation](docs/excel-pixel-conversion.md)

---

**Created**: 2025-01-01  
**Last Modified**: 2025-01-01  
**Version**: 1.0
