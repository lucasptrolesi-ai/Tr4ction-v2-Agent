# QUICK REFERENCE - TRILHAS EDUCACIONAIS

**Guia rápido de referência para desenvolvimento e testes**

---

## 🚀 INICIAR RÁPIDO

### Verificar se tudo está funcionando
```bash
# 1. Auditoria do sistema
python backend/audit_trail_system.py

# 2. Rodar testes
cd backend
pytest tests/test_trail_fidelity.py -v

# 3. Validar dependências
python -c "from app.services.question_extractor import Question; print('✅ OK')"
```

### Testar com template real
```bash
# Criar arquivo de teste
python -c "
from openpyxl import Workbook
wb = Workbook()
ws = wb.active
ws['A1'] = 'Diagnóstico'
ws['A3'] = 'Qual é seu desafio?'
ws.save('test_template.xlsx')
"

# Ingerir
python -c "
from app.services.trail_ingestion_service import TrailIngestionService
with open('test_template.xlsx', 'rb') as f:
    service = TrailIngestionService()
    questions, report = service.ingest(f.read())
    print(f'Perguntas: {len(questions)}')
    for q in questions:
        print(f'  [{q.order_index_global}] {q.question_text[:50]}')
"
```

---

## 📁 ARQUIVOS CHAVE

| Arquivo | Linhas | Função | Quick Access |
|---------|--------|--------|--------------|
| `question_extractor.py` | 600 | Extração | [def extract()](#) |
| `trail_ingestion_service.py` | 100 | Orquestração | [def ingest()](#) |
| `test_trail_fidelity.py` | 200 | Testes | pytest |
| `audit_trail_system.py` | 150 | Auditoria | python |

---

## 💡 SNIPPETS ÚTEIS

### 1. Usar TrailIngestionService
```python
from backend.app.services.trail_ingestion_service import TrailIngestionService

# Ler arquivo
with open('template.xlsx', 'rb') as f:
    file_bytes = f.read()

# Ingerir
service = TrailIngestionService()
questions, audit_report = service.ingest(file_bytes)

# Acessar resultados
for q in questions:
    print(f"Q{q.order_index_global}: {q.question_text}")
    print(f"  Aba: {q.sheet_name}, Seção: {q.section_name}")
    print(f"  Resposta em: {q.answer_cell_range}")

# Acessar auditoria
print(f"Snapshot status: {audit_report['step_1_snapshot']['status']}")
print(f"Perguntas extraídas: {len(audit_report['step_2_questions']['questions'])}")
print(f"Validação: {audit_report['step_3_validation']['status']}")
```

### 2. Extrair apenas perguntas
```python
from backend.app.services.question_extractor import QuestionExtractor

extractor = QuestionExtractor()
questions = extractor.extract(snapshot)  # snapshot é dict

# Iterar
for q in questions:
    print(f"{q.field_id}: {q.question_text}")
    if q.answer_cell_range:
        print(f"  → Responde em {q.answer_cell_range}")
```

### 3. Validar cobertura
```python
from backend.app.services.question_extractor import QuestionExtractor

extractor = QuestionExtractor()
questions = extractor.extract(snapshot)
is_valid, errors = extractor.validate_coverage(questions, snapshot)

if not is_valid:
    for error in errors:
        print(f"❌ {error}")
else:
    print(f"✅ Trilha válida com {len(questions)} perguntas")
```

### 4. Buscar pergunta por ID
```python
field_id = "abc123def"
question = next(
    q for q in questions 
    if q.field_id == field_id
)
print(f"Pergunta: {question.question_text}")
print(f"Ordem: {question.order_index_global}")
```

### 5. Agrupar por aba
```python
from collections import defaultdict

by_sheet = defaultdict(list)
for q in questions:
    by_sheet[q.sheet_name].append(q)

for sheet_name, sheet_questions in by_sheet.items():
    print(f"\n{sheet_name}:")
    for q in sheet_questions:
        print(f"  {q.order_index_sheet}. {q.question_text[:40]}...")
```

---

## 🧪 TESTES COMUNS

### Rodar testes específicos
```bash
# Um teste
pytest backend/tests/test_trail_fidelity.py::test_trail_order_sheets_preserved -v

# Múltiplos
pytest backend/tests/test_trail_fidelity.py::test_trail_* -v

# Com output
pytest backend/tests/test_trail_fidelity.py -v -s

# Com coverage
pytest backend/tests/test_trail_fidelity.py --cov=backend.app.services
```

### Debug de teste
```bash
# Parar no primeiro erro
pytest backend/tests/test_trail_fidelity.py -x

# Mostrar prints
pytest backend/tests/test_trail_fidelity.py -s

# Debugger
pytest backend/tests/test_trail_fidelity.py --pdb
```

### Criar fixture de teste
```python
# Em test_trail_fidelity.py
@pytest.fixture
def my_template_bytes():
    wb = Workbook()
    ws = wb.active
    ws['A1'] = 'Pergunta'
    ws['A2'] = 'Qual é?'
    
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

def test_my_case(my_template_bytes):
    service = TrailIngestionService()
    questions, _ = service.ingest(my_template_bytes)
    assert len(questions) == 1
```

---

## 🐛 DEBUGGING

### Problema: "Aba sem perguntas"
```bash
# Verificar snapshot
python -c "
from backend.app.services.template_snapshot import TemplateSnapshotService
with open('template.xlsx', 'rb') as f:
    service = TemplateSnapshotService()
    snapshot, _ = service.extract(f.read())
    
# Ver conteúdo
import json
for sheet_name, cells in snapshot['sheets'].items():
    print(f'{sheet_name}:')
    for cell in cells[:5]:
        print(f'  {cell[\"cell\"]}: {cell[\"value\"][:30]}'
"
```

### Problema: "order_index_global quebrada"
```python
# Debug de ordem
for i, q in enumerate(questions):
    if q.order_index_global != i:
        print(f"❌ Ordem quebrada: {i} != {q.order_index_global}")
        print(f"   Pergunta: {q.question_text[:50]}")
    else:
        print(f"✅ OK: {i}")
```

### Problema: "field_id não único"
```python
# Verificar duplicatas
from collections import Counter
ids = [q.field_id for q in questions]
duplicates = [id for id, count in Counter(ids).items() if count > 1]

if duplicates:
    print(f"❌ IDs duplicados: {duplicates}")
    for id in duplicates:
        for q in questions:
            if q.field_id == id:
                print(f"  → {q.question_text[:50]}")
else:
    print("✅ Todos IDs únicos")
```

---

## 📊 ANÁLISE

### Contar perguntas por aba
```bash
python -c "
from app.services.trail_ingestion_service import TrailIngestionService
import json

with open('template.xlsx', 'rb') as f:
    service = TrailIngestionService()
    questions, report = service.ingest(f.read())
    
    # Por aba
    from collections import defaultdict
    by_sheet = defaultdict(int)
    for q in questions:
        by_sheet[q.sheet_name] += 1
    
    for sheet, count in sorted(by_sheet.items()):
        print(f'{sheet}: {count} perguntas')
    
    print(f'Total: {len(questions)}')
"
```

### Ver tipos de pergunta detectados
```bash
python -c "
from app.services.trail_ingestion_service import TrailIngestionService
from collections import Counter

with open('template.xlsx', 'rb') as f:
    service = TrailIngestionService()
    questions, _ = service.ingest(f.read())
    
    types = Counter(q.inferred_type for q in questions)
    for type, count in types.items():
        print(f'{type}: {count}')
"
```

### Validar determinismo
```bash
python -c "
from app.services.trail_ingestion_service import TrailIngestionService

with open('template.xlsx', 'rb') as f:
    data = f.read()

# Ingeri 2x
service = TrailIngestionService()
q1, _ = service.ingest(data)
q2, _ = service.ingest(data)

# Comparar field_ids
for i in range(len(q1)):
    if q1[i].field_id != q2[i].field_id:
        print(f'❌ ID não determinístico em {i}')
    else:
        print(f'✅ {i}: {q1[i].field_id}')
"
```

---

## 🔄 INTEGRAÇÃO

### Integrar em admin_templates.py
```python
# ANTES
from backend.app.services.fillable_detector import FillableAreaDetector
detector = FillableAreaDetector()
candidates = detector.detect(snapshot)

# DEPOIS
from backend.app.services.trail_ingestion_service import TrailIngestionService
service = TrailIngestionService()
questions, audit = service.ingest(content)

# Usar questions ao invés de candidates
```

### Criar endpoint
```python
@router.get("/templates/{template_id}/trail")
async def get_trail(template_id: int, db: Session):
    questions = db.query(QuestionField).filter_by(
        template_id=template_id
    ).order_by(QuestionField.order_index_global).all()
    
    return {
        "questions": [
            {
                "field_id": q.field_id,
                "order": q.order_index_global,
                "text": q.question_text,
                "required": q.required,
            }
            for q in questions
        ]
    }
```

---

## 📚 DOCUMENTAÇÃO COMPLETA

| Documento | Conteúdo | Leia Se |
|-----------|----------|---------|
| `TRAIL_EDUCATION_ARCHITECTURE.md` | Arquitetura completa | Quer entender design |
| `INTEGRATION_GUIDE.md` | 7 passos de integração | Vai integrar |
| `TRAIL_EDUCATION_FINAL_REPORT.md` | Relatório executivo | Quer overview |
| `EXECUTIVE_SUMMARY_1PAGE.md` | 1 página resumida | Tem 5 minutos |
| `PROJECT_DASHBOARD.md` | Status e checklist | Quer ver progresso |
| Este arquivo | Quick reference | Está desenvolvendo |

---

## ⚙️ CONFIGURAÇÃO

### Variáveis de ambiente (opcional)
```bash
# Nenhuma necessária - sistema é genérico
# Mas pode customizar QUESTION_KEYWORDS se precisar

export QUESTION_KEYWORDS="qual,descreva,liste,explique,como,por que,quando,onde,quem"
export EXCLUDE_PATTERNS="exemplo,por exemplo,nota,obs,observação"
```

### Dependências
```bash
# Já instaladas em requirements.txt:
openpyxl==3.1.2
Pillow==10.1.0
lxml==4.9.3
python-dateutil==2.8.2

# Verificar
python -m pip list | grep -E "openpyxl|Pillow|lxml"
```

---

## 🎯 CHECKLIST DO DIA

### Manhã (30 min)
- [ ] Rodar `audit_trail_system.py`
- [ ] Rodar testes: `pytest tests/test_trail_fidelity.py -v`
- [ ] Verificar nenhum novo hardcode

### Tarde (2-3h)
- [ ] Integrar em `admin_templates.py`
- [ ] Criar `QuestionField` model
- [ ] Rodar migration BD
- [ ] Testar upload com template real

### Final do dia
- [ ] Criar endpoints GET /trail, POST /answer
- [ ] Teste E2E básico
- [ ] Commit código

---

## 🆘 TROUBLESHOOTING RÁPIDO

| Erro | Causa | Solução |
|------|-------|--------|
| `ImportError: No module named question_extractor` | Arquivo não existe | Verificar caminho: `backend/app/services/` |
| `TrailIngestionError: Aba X não tem perguntas` | Template não tem pergunta formal | Adicionar "Qual", "Descreva", etc |
| `order_index_global não sequencial` | Extração fora de ordem | Checar snapshot está ordenando por (row, col) |
| `field_id não determinístico` | Hash diferente cada vez | Bug raro - reportar com template |
| `test_trail_fidelity.py não encontrado` | Caminho errado | Estar em `backend/` antes de rodar pytest |

---

## 🚀 PRÓXIMAS AÇÕES

```
DIA 1 (hoje):
  - Você está aqui ✅
  - Ler arquitetura
  - Entender 9 passos

DIA 2 (amanhã):
  - Integrar admin_templates.py (1h)
  - Criar endpoints (1h)
  - Testar E2E (1h)

DIA 3:
  - Frontend com TemplateTrail (2-3h)
  - Bloqueios de avanço
  - Barra de progresso

DIA 4:
  - Validação final
  - Deploy
```

---

**QUICK REFERENCE COMPLETA**

Use esta página como seu guia rápido durante desenvolvimento.

Data: 18/01/2026
