# FCJ Template Ingestion - Guia Técnico

## Visão Geral

Este módulo implementa o **core semântico do método FCJ** no TR4CTION Agent V2. Transforma templates Excel em artefatos auditáveis, versionados e prontos para RAG/IA.

## Fluxo Completo

```
Upload Excel (.xlsx)
    ↓
TemplateSnapshotService (extração completa)
    ↓
validate_snapshot (auto-check obrigatório)
    ↓
FillableAreaDetector (detecção inteligente)
    ↓
TemplateStorageService (persistência)
    ↓
TemplateRegistry (DB + versionamento)
    ↓
Contexto para RAG + Agente TR4CTION
```

## Arquitetura

### 1. **TemplateSnapshotService** (`backend/app/services/template_snapshot.py`)

Extrai snapshot **completo e sem perda** de um arquivo Excel:

- **Workbook**: defined_names, sheetnames
- **Sheets** (para cada uma):
  - Cells: coordinate, value, formula, data_type, number_format, hyperlink, comment, **estilos completos**
  - Styles: font, fill (RGB), border, alignment, protection
  - Merged ranges
  - Row/Column dimensions (height, hidden, outline)
  - Data validations (tipo, fórmula, mensagens)
  - Conditional formatting
  - Tables
  - Images (binário + anchor)
  - Freeze panes
  - Page setup + margins

**Output:**
```json
{
  "schema_version": "2.0",
  "workbook": {...},
  "sheets": [
    {
      "name": "ICP",
      "cells": [...],
      "merged_cells": ["B3:D3"],
      "data_validations": [...],
      ...
    }
  ]
}
```

Compactado com gzip → `template.snapshot.json.gz`

### 2. **validate_snapshot** (validação obrigatória)

Função que valida presença de **todos os componentes críticos**:

```python
result = validate_snapshot(snapshot_dict)
# {
#   "valid": bool,
#   "errors": [lista de problemas],
#   "stats": {sheets_count, total_cells, ...}
# }
```

**Falha:** aborta ingestão com erro detalhado

### 3. **FillableAreaDetector** (`backend/app/services/fillable_detector.py`)

Detecta **áreas preenchíveis** usando heurísticas inteligentes:

#### Regras de Inclusão:
- ✅ Célula ou range vazio (fill branco/none)
- ✅ Sem fórmula
- ✅ Não é título (bold + tamanho >14 + cor)
- ✅ Não é exemplo ("Exemplo:", "Ex.:", etc)

#### Agrupamento em Blocos:
- Merged ranges = 1 bloco
- Células adjacentes compatíveis = expandir
- Resultado: `cell_range` (A1 ou A1:B3)

#### Inferência Semântica:
```
label         → buscar acima/esquerda (ignorar exemplos)
inferred_type → (choice | date | text_long | text_short | number)
phase         → (icp | persona | swot | journey | metrics)
example_value → texto curto do bloco
required      → true (padrão)
field_id      → SHA1(sheet|range|label)[:16] (determinístico)
```

**Output por campo:**
```python
FillableFieldCandidate(
    sheet="ICP",
    cell_range="B3:D3",
    label="Nome da Empresa",
    inferred_type="text_short",
    required=True,
    example_value=None,
    phase="icp",
    order_index=3001,  # sheet_index * 100000 + row * 1000 + col
    source_metadata={
        "is_merged": True,
        "has_validation": False,
        "detection_method": "merged_range",
        ...
    }
)
```

### 4. **TemplateStorageService** (`backend/app/services/template_storage.py`)

Persiste arquivos com versionamento por hash SHA-256:

```
{TEMPLATE_STORAGE_PATH}/
  {template_key}/
    {cycle}/
      {file_hash}/
        original.xlsx
        template.snapshot.json.gz
        assets.manifest.json
        assets/
          icp_image_0.png
          ...
```

**Idempotência:** Mesmo arquivo = mesmo hash = não duplica

### 5. **TemplateRegistry** (`backend/app/services/template_registry.py`)

Gerencia DB:

#### Tabelas:
- **template_definitions**
  - `(template_key, cycle, file_hash_sha256)` → UNIQUE
  - paths para storage
  - stats JSON
  - timestamps

- **fillable_fields**
  - `(template_id, field_id)` → UNIQUE
  - semântica FCJ (label, type, phase, order)
  - source_metadata JSON

#### Métodos Core:
```python
registry.compute_file_hash(file_bytes)              # SHA-256
registry.compute_template_key(filename, cycle)     # Chave estável
registry.compute_stats(snapshot, fields)           # Contadores

registry.upsert_template_definition(...)           # Idempotente
registry.replace_fields_for_template(...)          # Atômico

registry.get_template_with_fields(db, template_id) # Completo + ordenado
```

## Endpoints Admin

### POST /admin/templates/upload

**Upload e ingestão completa**

```bash
curl -X POST "http://localhost:8000/admin/templates/upload?cycle=Q1" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -F "file=@template_fcj.xlsx"
```

**Retorna:**
```json
{
  "message": "Template FCJ ingested successfully",
  "template_id": 123,
  "template_key": "q1_template_fcj",
  "cycle": "Q1",
  "file_hash_sha256": "abc123...",
  "paths": {
    "original_path": "/abs/path/original.xlsx",
    "snapshot_path": "/abs/path/template.snapshot.json.gz"
  },
  "stats": {
    "num_sheets": 3,
    "num_cells": 245,
    "num_fields": 18
  },
  "fields_count": 18
}
```

### GET /admin/templates/{template_id}

**Detalhes + fields ordenados**

```bash
curl -H "Authorization: Bearer <ADMIN_TOKEN>" \
  "http://localhost:8000/admin/templates/123"
```

**Retorna:**
```json
{
  "template": {
    "id": 123,
    "template_key": "q1_template_fcj",
    "cycle": "Q1",
    "stats": {...}
  },
  "fields": [
    {
      "id": 1,
      "field_id": "abc123",
      "sheet_name": "ICP",
      "cell_range": "B3:D3",
      "label": "Nome da Empresa",
      "inferred_type": "text_short",
      "required": true,
      "phase": "icp",
      "order_index": 3001,
      ...
    },
    ...
  ]
}
```

### GET /admin/templates/{template_id}/snapshot

**Snapshot JSON descompactado** (debug)

### GET /admin/templates/{template_id}/context

**Contexto otimizado para RAG/Agente TR4CTION**

```json
{
  "template_meta": {
    "id": 123,
    "template_key": "q1_template_fcj",
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
      "order": 3001
    },
    ...
  ],
  "phases_summary": {
    "icp": [
      {"label": "Nome da Empresa", "type": "text_short", ...},
      ...
    ],
    "persona": [...],
    "swot": [...]
  }
}
```

## Variáveis de Ambiente

```bash
# Onde snapshots/assets são salvos
TEMPLATE_STORAGE_PATH=/abs/path/to/storage

# Fallback (se não set acima)
DATA_DIR=/abs/path/to/backend/data
```

## Validação de Snapshot

A validação é **obrigatória** no pipeline. Se falhar:

```
SnapshotValidationError: Snapshot INVÁLIDO:
  - Sheet 'ICP': data_validations ausente
  - Sheet 'ICP': células sem estilo
```

## Testes

```bash
# Teste de snapshot completeness
pytest backend/app/tests/test_snapshot_completeness.py -v

# Teste de fillable detection
pytest backend/app/tests/test_fillable_detector_blocks.py -v

# Teste de integração (pipeline completo)
pytest backend/app/tests/test_admin_upload_pipeline.py -v -s
```

## Integração com Agente TR4CTION

O Agente consome via:

```python
# No serviço de RAG/chat
template_context = requests.get(
    f"http://localhost:8000/admin/templates/{template_id}/context",
    headers={"Authorization": f"Bearer {admin_token}"}
).json()

# Usa:
# - template_context["fillable_fields"] → lista campos + tipos + labels
# - template_context["phases_summary"] → agrupa por fase FCJ
# - Cada field tem "example" e "label" para sugerir ao usuário
```

## Garantias do Sistema

- ✅ **Sem perda de informação** → snapshot completo
- ✅ **Auditável** → JSON estruturado + versionamento
- ✅ **Determinístico** → field_id estável
- ✅ **Escalável** → suporta qualquer template FCJ
- ✅ **Idempotente** → upload repetido = mesmo resultado
- ✅ **Validado** → auto-check em cada etapa
- ✅ **RAG-ready** → contexto otimizado para IA

## Estrutura de Diretórios

```
backend/app/
├── services/
│   ├── template_snapshot.py      # Extração
│   ├── template_storage.py       # Persistência
│   ├── fillable_detector.py      # Detecção
│   └── template_registry.py      # Banco
├── models/
│   └── template_definition.py    # SQLAlchemy models
├── db/
│   ├── migrations/versions/
│   │   └── 001_fcj_templates.py  # Alembic
│   └── session.py
├── tests/
│   ├── test_snapshot_completeness.py
│   ├── test_fillable_detector_blocks.py
│   └── test_admin_upload_pipeline.py
└── routers/
    └── (admin_templates.py em backend/routers/)
```

## Próximos Passos

1. ✅ Core pipeline implementado
2. ✅ DB migrations criadas
3. ✅ Endpoints admin finalizados
4. ✅ Testes de integração
5. 🔄 Deployment em produção
6. 📊 Monitoramento + observabilidade

---

**Versão:** 2.0  
**Data:** 14 Jan 2026  
**Status:** Production Ready ✓
