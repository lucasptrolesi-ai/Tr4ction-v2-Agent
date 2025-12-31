# 📚 Guia de Ingestão Automática de Templates - Admin

## 🎯 Visão Geral

Este sistema permite que **administradores FCJ** façam upload de novos arquivos Excel (Template_Q2.xlsx, Template_Q3.xlsx, etc.) e **automaticamente** tornem todos os templates disponíveis para founders, sem necessidade de código ou configuração manual.

---

## 🚀 Como Funciona

### Pipeline Automático

```
1. Admin faz upload do Excel → 2. Sistema processa sheets → 
3. Gera JSON schemas → 4. Exporta PNGs → 5. Registra no banco → 
6. Templates disponíveis instantaneamente
```

### Características

- ✅ **100% genérico** - funciona com qualquer cycle (Q1, Q2, Q3, Q4, etc.)
- ✅ **Zero código** - nenhuma alteração necessária no sistema
- ✅ **Validação automática** - detecta erros e gera relatório
- ✅ **Descoberta dinâmica** - founders veem novos templates automaticamente
- ✅ **Compatível com AI Mentor** - funciona sem mudanças na IA

---

## 📋 Pré-requisitos

### Acesso Admin

Você precisa estar logado com uma conta **admin** (não founder).

**Credenciais padrão de desenvolvimento:**
- Email: `admin@fcj.com.br`
- Senha: `admin123`

### Arquivo Excel Válido

O arquivo deve:
- Ser formato `.xlsx` (Excel 2007+)
- Conter uma ou mais sheets com templates
- Usar formatação padrão: células editáveis = fundo branco + bordas finas

---

## 🔧 Como Fazer Upload

### Método 1: API REST (Recomendado)

#### Endpoint

```
POST /admin/templates/upload
```

#### Headers

```
Authorization: Bearer <seu_token_admin>
Content-Type: multipart/form-data
```

#### Body (form-data)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `file` | File | ✅ | Arquivo Excel (.xlsx) |
| `cycle` | String | ✅ | Identificador do cycle (ex: "Q2", "Q3") |
| `description` | String | ❌ | Descrição opcional |

#### Exemplo com cURL

```bash
curl -X POST "http://localhost:8000/admin/templates/upload" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "file=@Template_Q2.xlsx" \
  -F "cycle=Q2" \
  -F "description=Templates Q2 2025"
```

#### Exemplo com Python

```python
import requests

url = "http://localhost:8000/admin/templates/upload"
headers = {"Authorization": "Bearer YOUR_ADMIN_TOKEN"}
files = {"file": open("Template_Q2.xlsx", "rb")}
data = {
    "cycle": "Q2",
    "description": "Templates Q2 2025"
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

#### Exemplo com JavaScript (Frontend)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('cycle', 'Q2');
formData.append('description', 'Templates Q2 2025');

const response = await fetch('http://localhost:8000/admin/templates/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${adminToken}`
  },
  body: formData
});

const result = await response.json();
console.log(result);
```

### Método 2: Interface Web (Futura)

Uma interface de admin será implementada em `/admin/templates` com:
- Drag & drop de arquivos
- Preenchimento de formulário (cycle, description)
- Visualização de progresso
- Histórico de uploads

---

## 📊 Resposta da API

### Sucesso (200 OK)

```json
{
  "success": true,
  "data": {
    "cycle": "Q2",
    "total_sheets": 26,
    "successful": 26,
    "failed": 0,
    "total_fields": 647,
    "registered_in_db": 26,
    "report_path": "backend/TEMPLATE_INGESTION_REPORT_Q2.md",
    "results": [
      {
        "template_key": "cronograma",
        "sheet_name": "Cronograma",
        "success": true,
        "field_count": 38,
        "schema_path": "backend/templates/generated/Q2/cronograma.json",
        "image_path": "frontend/public/templates/Q2/cronograma.png",
        "warnings": [],
        "errors": []
      }
      // ... mais templates
    ]
  }
}
```

### Erro (4xx/5xx)

```json
{
  "success": false,
  "detail": "Only .xlsx files are supported",
  "code": "INVALID_FILE_TYPE"
}
```

---

## 📁 Estrutura de Arquivos Gerada

### Após Upload Bem-Sucedido

```
backend/
  data/
    templates_source/
      Q2/                              ← Arquivo Excel original salvo aqui
        Template_Q2.xlsx
  templates/
    generated/
      Q2/                              ← Schemas JSON gerados
        cronograma.json
        1_0_diagnostico.json
        3_1_persona_01.json
        ...

frontend/
  public/
    templates/
      Q2/                              ← Imagens PNG geradas
        cronograma.png
        1_0_diagnostico.png
        3_1_persona_01.png
        ...

backend/
  TEMPLATE_INGESTION_REPORT_Q2.md      ← Relatório detalhado
```

---

## 📄 Relatório de Ingestão

### Localização

Após cada upload, um relatório é gerado em:

```
backend/TEMPLATE_INGESTION_REPORT_{cycle}.md
```

Exemplo: `TEMPLATE_INGESTION_REPORT_Q2.md`

### Conteúdo do Relatório

- **Summary**: Total de templates processados, sucessos, falhas, campos gerados
- **Processed Templates**: Tabela com status de cada template
- **Warnings**: Avisos não-críticos (campos sem labels, etc.)
- **Errors**: Erros críticos que impediram processamento
- **Validation**: Validação automática (schemas, PNGs, overlay integrity)

### Exemplo

```markdown
# Template Ingestion Report - Q2

**Generated**: 2025-12-31T20:30:00.000000
**Source File**: /path/to/Template_Q2.xlsx
**Cycle**: Q2

## Summary

- **Total templates processed**: 26
- **Successful**: 26
- **Failed**: 0
- **Total fields generated**: 647

## Processed Templates

| Template Key | Sheet Name | Status | Fields | Warnings |
|--------------|------------|--------|--------|----------|
| cronograma | Cronograma | ✅ | 38 | 7 |
| 3_1_persona_01 | 3.1 Persona 01 | ✅ | 32 | 0 |
...
```

---

## 🔍 Verificando Templates Disponíveis

### Listar Cycles Disponíveis

```bash
GET /api/templates/cycles
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "cycles": ["Q1", "Q2", "Q3"],
    "total": 3
  }
}
```

### Listar Templates de um Cycle

```bash
GET /api/templates/Q2
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "cycle": "Q2",
    "templates": [
      {
        "cycle": "Q2",
        "template_key": "cronograma",
        "sheet_name": "Cronograma",
        "schema_path": "backend/templates/generated/Q2/cronograma.json",
        "image_path": "frontend/public/templates/Q2/cronograma.png",
        "status": "active",
        "field_count": 38
      }
      // ... mais templates
    ],
    "total": 26
  }
}
```

### Buscar Template Específico

```bash
GET /api/templates/Q2/cronograma
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "cycle": "Q2",
    "template_key": "cronograma",
    "sheet_name": "Cronograma",
    "schema_path": "...",
    "image_path": "...",
    "field_count": 38,
    "schema": {
      "template_key": "cronograma",
      "sheet_name": "Cronograma",
      "sheet_width": 1200.5,
      "sheet_height": 800.3,
      "fields": [
        {
          "key": "field_b10_0",
          "label": "Atividade 1",
          "cell": "B10",
          "type": "text",
          "top": 150.5,
          "left": 70.0,
          "width": 200.0,
          "height": 20.0
        }
        // ... mais campos
      ]
    }
  }
}
```

---

## 🔄 Gerenciamento de Templates

### Ativar/Desativar Template

```bash
PATCH /admin/templates/{template_id}/status
Authorization: Bearer YOUR_ADMIN_TOKEN
Content-Type: application/json

{
  "status": "inactive"  # ou "active", "archived"
}
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "cycle": "Q2",
    "template_key": "cronograma",
    "status": "inactive"
  }
}
```

### Listar Todos os Templates (Admin)

```bash
GET /admin/templates?cycle=Q2
Authorization: Bearer YOUR_ADMIN_TOKEN
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "templates": [...],
    "total": 26
  }
}
```

---

## ⚙️ Detalhes Técnicos

### Normalização de Template Keys

Nomes de sheets são automaticamente normalizados:

| Sheet Name Original | Template Key Gerado |
|---------------------|---------------------|
| `3.1 Persona 01` | `3_1_persona_01` |
| `10.1 OKRs e KPIs` | `10_1_okrs_e_kpis` |
| `Canvas de Diferenciação` | `canvas_de_diferenciacao` |

**Regras:**
- Remove acentos
- Converte para lowercase
- Substitui espaços e pontos por `_`
- Remove caracteres especiais
- Remove underscores duplicados

### Detecção de Células Editáveis

**Heurística usada:**
1. Fill color é **BRANCO** (rgb = "FFFFFFFF" ou theme = 0)
2. Borders são **THIN** nos 4 lados (left, right, top, bottom)
3. Célula não está merged **OU** é a célula anchor de um merge

### Extração de Labels

Para cada célula editável, o sistema busca um label:
1. **Olha à ESQUERDA** (até 8 colunas) na mesma linha
2. Se não encontrar, **olha para CIMA** (até 12 linhas) na mesma coluna
3. Label válido = célula com fill não-branco **OU** fonte bold

### Conversão Pixel-Perfect

O sistema usa as mesmas constantes do Persona 01:

```python
EXCEL_COLUMN_UNIT_TO_PIXELS = 7.0
EXCEL_ROW_POINT_TO_PIXELS = 1.33
TEXTAREA_HEIGHT_THRESHOLD = 40.0  # pixels (~2 rows)
```

### Tipos de Campos

- **text**: Campos com altura < 40px (1 linha)
- **textarea**: Campos com altura >= 40px (2+ linhas)

---

## 🐛 Troubleshooting

### Problema: "No editable cells discovered"

**Causa:** Sheet não possui células que atendem aos critérios (branco + bordas finas).

**Solução:**
1. Abra o Excel e verifique a formatação das células
2. Certifique-se que células editáveis têm:
   - Fundo branco
   - Bordas finas nos 4 lados
3. Ou crie um arquivo de override manual em:
   ```
   backend/tools/template_overrides/{template_key}.json
   ```

### Problema: "Many warnings about missing labels"

**Causa:** Células editáveis não têm labels próximos detectáveis.

**Solução:**
1. **Aceite os warnings** se os campos são realmente sem label (ex: tabelas)
2. **Ajuste o Excel**: adicione labels em células com fill colorido ou bold
3. **Ignore se não for crítico**: founders ainda podem usar o template

### Problema: Upload falha com erro 500

**Causa:** Arquivo corrompido ou formato inválido.

**Solução:**
1. Verifique se é `.xlsx` (não `.xls` antigo)
2. Abra no Excel e salve novamente
3. Verifique logs do backend: `backend/template_generation.log`

### Problema: Template não aparece no frontend

**Causa:** Status pode estar "inactive" ou banco não sincronizado.

**Solução:**
1. Verifique se o template está ativo:
   ```bash
   GET /admin/templates?cycle=Q2
   ```
2. Se estiver "inactive", ative:
   ```bash
   PATCH /admin/templates/{id}/status
   Body: {"status": "active"}
   ```
3. Verifique se arquivos existem:
   ```bash
   ls backend/templates/generated/Q2/
   ls frontend/public/templates/Q2/
   ```

---

## 🎓 Exemplo Completo: Upload Template Q3

### 1. Preparar Arquivo

Arquivo: `Template_Q3.xlsx`
- 30 sheets com templates
- Formatação padrão FCJ

### 2. Fazer Upload via API

```bash
curl -X POST "http://localhost:8000/admin/templates/upload" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -F "file=@Template_Q3.xlsx" \
  -F "cycle=Q3" \
  -F "description=Templates Q3 2025 - Expansão Internacional"
```

### 3. Aguardar Processamento

**Tempo estimado:** 30-60 segundos para 30 templates

Console mostrará:
```
🚀 Starting ingestion for cycle 'Q3'
Found 30 sheets: ['Cronograma', '1.0 Diagnóstico', ...]
✅ Processed template 'cronograma' - 38 fields
✅ Processed template '1_0_diagnostico' - 1 field
...
✅ Ingestion complete - 30/30 templates registered
```

### 4. Verificar Relatório

Abrir: `backend/TEMPLATE_INGESTION_REPORT_Q3.md`

```markdown
# Template Ingestion Report - Q3

## Summary

- **Total templates processed**: 30
- **Successful**: 30
- **Failed**: 0
- **Total fields generated**: 715

## Status

✅ **INGESTION SUCCESSFUL** - All templates ready for use
```

### 5. Verificar Disponibilidade

```bash
# Listar cycles
GET /api/templates/cycles
# Resposta: {"cycles": ["Q1", "Q2", "Q3"], "total": 3}

# Listar templates Q3
GET /api/templates/Q3
# Resposta: 30 templates
```

### 6. Testar no Frontend

1. Founder faz login
2. Navega para `/founder/templates`
3. Seleciona "Q3" no dropdown de cycles
4. Vê 30 templates disponíveis
5. Abre qualquer template e preenche

**Funciona imediatamente sem deploy ou restart!**

---

## 📝 Boas Práticas

### Convenções de Naming

- **Cycles:** Use formato `Q{número}` (Q1, Q2, Q3, Q4)
- **Descrições:** Inclua ano e contexto (ex: "Templates Q2 2025 - Marketing Digital")

### Versionamento

Se precisar atualizar templates de um cycle:

1. **Reupload com mesmo cycle:** Templates existentes serão **atualizados**
2. **Templates novos:** Serão **adicionados**
3. **Templates removidos:** Permanecerão inativos (não são deletados)

**Exemplo:**
```bash
# Primeiro upload Q2
POST /admin/templates/upload
  file: Template_Q2_v1.xlsx
  cycle: Q2
# → 26 templates criados

# Atualização Q2 (novas sheets adicionadas)
POST /admin/templates/upload
  file: Template_Q2_v2.xlsx
  cycle: Q2
# → 26 templates atualizados + 4 novos = 30 templates
```

### Validação Manual

Após cada upload, recomenda-se:

1. ✅ Ler relatório de ingestão
2. ✅ Verificar warnings/errors
3. ✅ Testar 2-3 templates no frontend
4. ✅ Validar overlay positioning
5. ✅ Confirmar labels corretos

### Backup

Arquivos originais são preservados em:
```
backend/data/templates_source/{cycle}/
```

**Nunca delete esses arquivos!** São a source of truth para regeneração.

---

## 🚨 Limitações Conhecidas

1. **PNGs são placeholders:** Sistema gera PNGs com grid genérico. Para produção, recomenda-se:
   - Instalar LibreOffice headless
   - Ou exportar PNGs manualmente do Excel
   - Ou usar screenshots de alta qualidade

2. **Heurística pode falhar:** Em templates com formatação muito diferente, a detecção pode não funcionar. Solução: criar overrides manuais.

3. **Excel 2007+ apenas:** Arquivos `.xls` antigos não são suportados.

---

## 💡 Dicas Avançadas

### Regenerar Templates de um Cycle

Se precisar reprocessar todos os templates de um cycle:

```bash
# 1. Faça upload novamente do mesmo arquivo
POST /admin/templates/upload
  file: Template_Q2.xlsx
  cycle: Q2

# 2. Sistema detecta cycle existente e atualiza tudo
```

### Criar Override Manual

Para templates com formatação especial:

```json
// backend/tools/template_overrides/golden_circle.json
{
  "editable_cells": ["B5", "D8", "F12", "H15"],
  "labels": {
    "B5": "Por quê?",
    "D8": "Como?",
    "F12": "O quê?",
    "H15": "Resultado"
  }
}
```

### Integração CI/CD

Para automação completa:

```yaml
# .github/workflows/update-templates.yml
name: Update Templates

on:
  push:
    paths:
      - 'templates/*.xlsx'

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - name: Upload to API
        run: |
          curl -X POST "${{ secrets.API_URL }}/admin/templates/upload" \
            -H "Authorization: Bearer ${{ secrets.ADMIN_TOKEN }}" \
            -F "file=@templates/Template_Q2.xlsx" \
            -F "cycle=Q2"
```

---

## 📞 Suporte

**Problemas técnicos:**
- Verifique logs: `backend/template_generation.log`
- Leia relatório de ingestão: `backend/TEMPLATE_INGESTION_REPORT_{cycle}.md`
- Consulte desenvolvedor backend

**Dúvidas sobre uso:**
- Este guia cobre 99% dos casos
- Para casos especiais, consulte equipe técnica

---

## ✅ Checklist de Sucesso

Após fazer upload de um novo cycle, confirme:

- [ ] Relatório gerado sem erros críticos
- [ ] Todos os templates listados em `/api/templates/{cycle}`
- [ ] Arquivos JSON existem em `backend/templates/generated/{cycle}/`
- [ ] Arquivos PNG existem em `frontend/public/templates/{cycle}/`
- [ ] Founders conseguem ver templates no frontend
- [ ] Ao menos 1 template testado end-to-end (preenchimento + export)
- [ ] AI Mentor funciona com novos templates

---

**Última atualização:** 31/12/2025
**Versão do sistema:** 1.0.0
