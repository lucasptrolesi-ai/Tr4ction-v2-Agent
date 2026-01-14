# FCJ Template Ingestion Module - Documentação Técnica

## 📋 Visão Geral

Módulo production-ready para ingestão, análise e gestão de templates Excel do **método FCJ (Founder's Compass Journey)**.

### Garantias do Sistema

✅ **Extração sem perda**: Snapshot completo com validação obrigatória  
✅ **Detecção inteligente**: Fillable areas identificadas por heurísticas semânticas  
✅ **Versionamento SHA-256**: Idempotência e auditabilidade completa  
✅ **Escalabilidade**: Suporta qualquer template FCJ sem hardcode  
✅ **RAG-ready**: Contexto estruturado para Agente TR4CTION  

---

## 🏗️ Arquitetura

```
backend/app/
├── services/
│   ├── template_snapshot.py      # Extração completa + validação
│   ├── fillable_detector.py      # Detecção de áreas preenchíveis
│   ├── template_storage.py       # Persistência versionada
│   └── template_registry.py      # DB + stats
├── models/
│   └── template_definition.py    # TemplateDefinition + FillableField
├── db/migrations/versions/
│   └── 001_fcj_templates.py      # Alembic migration
└── tests/
    ├── test_snapshot_completeness.py
    ├── test_fillable_detector_blocks.py
    └── test_admin_upload_pipeline.py

backend/routers/
└── admin_templates.py             # Endpoints admin
```

---

## 🚀 Quickstart

### 1. Rodar Migrations

```bash
cd backend
alembic upgrade head
```

### 2. Configurar Storage (opcional)

```bash
# .env
TEMPLATE_STORAGE_PATH=/path/to/templates/storage
DATA_DIR=/path/to/data  # fallback
```

### 3. Upload de Template

```bash
curl -X POST "http://localhost:8000/admin/templates/upload?cycle=Q1" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -F "file=@./template_icp_q1.xlsx"
```

**Resposta esperada:**

```json
{
  "message": "Template FCJ ingested successfully",
  "template_id": 1,
  "template_key": "q1_template_icp_q1",
  "cycle": "Q1",
  "file_hash_sha256": "abc123...",
  "paths": {
    "original_path": "/storage/q1_template_icp_q1/Q1/abc123.../original.xlsx",
    "snapshot_path": "/storage/.../template.snapshot.json.gz",
    "assets_manifest_path": "/storage/.../assets.manifest.json"
  },
  "stats": {
    "num_sheets": 1,
    "num_cells": 45,
    "num_merged": 3,
    "num_images": 0,
    "num_validations": 2,
    "num_fields": 8
  },
  "validation_report": {
    "valid": true,
    "errors": [],
    "stats": {...}
  },
  "fields_count": 8
}
```

### 4. Consultar Template

```bash
# Listar todos
curl "http://localhost:8000/admin/templates" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Detalhes + fields
curl "http://localhost:8000/admin/templates/1" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Snapshot raw
curl "http://localhost:8000/admin/templates/1/snapshot" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Contexto para RAG
curl "http://localhost:8000/admin/templates/1/context" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

---

## 📦 Pipeline de Ingestão

### Fluxo Completo (POST /upload)

```
1. Validar .xlsx                              [FastAPI]
2. Extrair snapshot completo                  [TemplateSnapshotService]
   └─> workbook props + sheets + cells + styles + validations + images
3. Validar snapshot (self-check obrigatório)  [validate_snapshot]
   └─> Aborta se faltar componente crítico
4. Detectar fillable areas                    [FillableAreaDetector]
   └─> Heurísticas: merged ranges, validations, proximidade de labels
5. Persistir storage                          [TemplateStorageService]
   └─> {template_key}/{cycle}/{hash}/
       ├── original.xlsx
       ├── template.snapshot.json.gz
       └── assets/
6. Computar stats                             [TemplateRegistry]
7. Upsert DB (idempotente por hash)           [TemplateRegistry]
8. Replace fields (delete + insert)           [TemplateRegistry]
9. Commit transaction
10. Retornar relatório completo
```

---

## 🔍 Detecção de Fillable Areas

### Heurísticas Aplicadas

#### ✅ **Candidatos Válidos**

- Células ou merged ranges com:
  - Fill branco/vazio
  - Value vazio OU placeholder curto (<200 chars)
  - Sem fórmula
  - Estilo não-título (sem bold+grande+colorido)
  - Texto não contém "Exemplo", "Ex:", etc.

#### 🚫 **Exclusões Automáticas**

- Células com fórmulas
- Títulos (bold + size >= 14 + fill colorido)
- Exemplos explícitos
- Texto muito longo (> 200 chars)

#### 🧠 **Inferências Semânticas**

| Regra | Tipo Inferido |
|-------|---------------|
| Data validation list | `choice` |
| Number format com date | `date` |
| Range >= 4 células | `text_long` |
| Data type numérico | `number` |
| Default | `text_short` |

#### 🏷️ **Labels**

- Busca em janela 3x3 acima e à esquerda
- Prioriza texto acima (mesma coluna)
- Ignora exemplos e células vazias

#### 🎯 **Phase FCJ**

- Inferida por nome da sheet + labels próximos
- Phases conhecidas: `icp`, `persona`, `swot`, `journey`, `metrics`

---

## 💾 Storage Structure

```
{TEMPLATE_STORAGE_PATH}/
└── {template_key}/
    └── {cycle}/
        └── {file_hash_sha256}/
            ├── original.xlsx
            ├── template.snapshot.json.gz
            ├── assets/
            │   ├── ICP_image_0.png
            │   └── Persona_image_0.png
            └── assets.manifest.json
```

### Snapshot Schema v2.0

```json
{
  "schema_version": "2.0",
  "workbook": {
    "defined_names": {},
    "sheetnames": ["ICP", "Persona"]
  },
  "sheets": [
    {
      "name": "ICP",
      "cells": [
        {
          "coordinate": "A1",
          "value": "Nome da Empresa:",
          "data_type": "s",
          "number_format": "General",
          "style": {
            "font": {"bold": true, "size": 11, "color": null},
            "fill": {"patternType": null, "fgColor": null},
            "border": {...},
            "alignment": {...},
            "protection": {...}
          }
        }
      ],
      "merged_cells": ["B1:C1"],
      "data_validations": [...],
      "row_dimensions": [...],
      "column_dimensions": [...],
      "conditional_formatting": [...],
      "tables": [...],
      "images": [...]
    }
  ]
}
```

---

## 🗄️ Database Schema

### `template_definitions`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | PK |
| `template_key` | String(255) | Chave estável (cycle + filename) |
| `cycle` | String(50) | Q1, Q2, Q3, Q4, etc. |
| `file_hash_sha256` | String(64) | Hash para versionamento |
| `original_path` | String(500) | Path do .xlsx |
| `snapshot_path` | String(500) | Path do snapshot.json.gz |
| `assets_manifest_path` | String(500) | Path do manifest de assets |
| `stats_json` | Text | Stats serializados |
| `created_at` | DateTime | Timestamp |
| `updated_at` | DateTime | Timestamp |

**Índices:**
- UNIQUE: `(template_key, cycle, file_hash_sha256)`
- Index: `template_key`, `cycle`

### `fillable_fields`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | PK |
| `template_id` | Integer | FK -> template_definitions |
| `field_id` | String(16) | Hash estável (sheet+range+label) |
| `sheet_name` | String(255) | Nome da aba |
| `cell_range` | String(50) | A1 ou A1:B2 |
| `label` | String(255) | Label inferido |
| `inferred_type` | String(50) | choice/date/text_short/text_long/number |
| `required` | Boolean | Sempre true por padrão |
| `example_value` | Text | Valor de exemplo (se detectado) |
| `phase` | String(50) | icp/persona/swot/journey/metrics |
| `order_index` | Integer | Ordem visual (sheet*100000 + row*1000 + col) |
| `source_metadata_json` | Text | Metadados da detecção |
| `created_at` | DateTime | Timestamp |

**Índices:**
- UNIQUE: `(template_id, field_id)`
- Index: `template_id`, `sheet_name`, `phase`, `order_index`

---

## 🧪 Testes

### Rodar Suite Completa

```bash
cd backend/app
pytest tests/ -v
```

### Testes Disponíveis

1. **test_snapshot_completeness.py**
   - Extração de workbook básico
   - Data validations
   - Merged cells + estilos
   - Validação pass/fail

2. **test_fillable_detector_blocks.py**
   - Detecção de merged ranges
   - Células com validation
   - Exclusão de títulos
   - Exclusão de exemplos
   - Inferência de labels
   - Estabilidade de field_id

3. **test_admin_upload_pipeline.py**
   - Pipeline end-to-end
   - Idempotência por hash
   - Recuperação com fields ordenados

---

## 🤖 Integração com Agente TR4CTION

### Endpoint Especializado

```bash
GET /admin/templates/{template_id}/context
```

**Retorno otimizado para RAG:**

```json
{
  "template_meta": {
    "id": 1,
    "template_key": "q1_icp",
    "cycle": "Q1",
    "stats": {...}
  },
  "fillable_fields": [
    {
      "field_id": "abc123",
      "sheet": "ICP",
      "label": "Nome da Empresa",
      "type": "text_short",
      "required": true,
      "example": null,
      "phase": "icp",
      "order": 1001
    }
  ],
  "phases_summary": {
    "icp": [
      {"label": "Nome da Empresa", "type": "text_short", "required": true},
      {"label": "Segmento", "type": "choice", "required": true}
    ]
  }
}
```

### Uso no RAG

```python
from app.services.template_registry import TemplateRegistry

def get_fcj_context_for_chat(template_id: int, db: Session) -> str:
    registry = TemplateRegistry()
    context = registry.get_template_with_fields(db, template_id)
    
    # Formatar para prompt do LLM
    fields_text = "\n".join([
        f"- {f['label']} ({f['inferred_type']}): {f['example_value'] or 'preenchimento livre'}"
        for f in context["fields"]
    ])
    
    return f"""
Template FCJ: {context['template']['template_key']}
Cycle: {context['template']['cycle']}

Campos obrigatórios:
{fields_text}

Instrução: Orientar o founder no preenchimento destes campos de forma estratégica.
"""
```

---

## 🔒 Segurança e Observabilidade

### Logs Estruturados

Todos os serviços usam `logging` com níveis apropriados:

```python
logger.info(f"✓ Snapshot validado: {len(snapshot['sheets'])} sheets")
logger.error(f"❌ Erro na ingestão: {e}", exc_info=True)
```

### Validação Obrigatória

- Snapshot auto-validado no `extract()`
- Lança `SnapshotValidationError` se incompleto
- Aborta ingestão para evitar dados corrompidos

### Idempotência

- Hash SHA-256 garante uniqueness
- Upsert no DB evita duplicação
- Mesmo arquivo = mesmo registro

---

## 📊 Métricas e Stats

Computados automaticamente:

```json
{
  "num_sheets": 2,
  "num_cells": 145,
  "num_merged": 8,
  "num_images": 2,
  "num_validations": 5,
  "num_tables": 0,
  "num_fields": 12,
  "schema_version": "2.0"
}
```

---

## 🛠️ Troubleshooting

### Erro: "Snapshot INVÁLIDO"

**Causa:** Extração incompleta (faltando estilos, validations, etc.)

**Solução:** Verificar `template_snapshot.py` - todos os componentes devem estar presentes.

### Erro: "Nenhum campo detectado"

**Causa:** Heurísticas muito restritivas ou template apenas com títulos.

**Solução:** Revisar `fillable_detector.py` - ajustar regras de exclusão.

### Performance: Upload lento

**Causa:** Arquivo muito grande (>10MB) ou muitas imagens.

**Solução:** 
- Aumentar `REQUEST_SIZE_LIMIT` no middleware
- Considerar processamento assíncrono para assets

---

## 🔄 Versionamento

- **Schema Version**: `2.0`
- **Migration**: `001_fcj_templates`
- **Alembic**: Compatible

---

## 📞 Suporte

Para dúvidas ou issues:
1. Verificar logs estruturados
2. Rodar testes: `pytest tests/ -v`
3. Validar snapshot manualmente: `validate_snapshot(snapshot_dict)`

---

## ✅ Checklist de Produção

- [x] Extração completa sem perda
- [x] Validação obrigatória
- [x] Detecção inteligente de fields
- [x] Versionamento SHA-256
- [x] Storage organizado
- [x] Migrations Alembic
- [x] Testes automatizados
- [x] Endpoints admin seguros
- [x] Contexto RAG-ready
- [x] Logs estruturados
- [x] Documentação completa

---

**Sistema pronto para produção e escalável para novos templates FCJ. 🚀**
