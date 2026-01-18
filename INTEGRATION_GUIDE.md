# GUIA DE INTEGRAÇÃO - TRILHAS EDUCACIONAIS

**Objetivo**: Integrar o sistema de trilhas educacionais no pipeline existente  
**Tempo Estimado**: 6-7 horas  
**Dificuldade**: Média  

---

## ✅ PASSO 1: Atualizar admin_templates.py (1h)

**Arquivo**: `backend/routers/admin_templates.py`

### Antes (Antigo)

```python
from backend.app.services.fillable_detector import FillableAreaDetector

@router.post("/upload")
async def upload_template(file: UploadFile, cycle: str, db: Session):
    content = await file.read()
    
    # Snapshot
    snapshot_service = TemplateSnapshotService()
    snapshot, assets = snapshot_service.extract(content)
    
    # Detectar campos ❌ ANTIGO
    detector = FillableAreaDetector()
    candidates = detector.detect(snapshot)
    
    # Salvar
    for candidate in candidates:
        db.add(FillableFieldCandidate(...))
```

### Depois (Novo)

```python
from backend.app.services.trail_ingestion_service import TrailIngestionService

@router.post("/upload")
async def upload_template(file: UploadFile, cycle: str, db: Session):
    content = await file.read()
    
    try:
        # ✅ NOVO: Usar TrailIngestionService
        trail_service = TrailIngestionService()
        questions, audit_report = trail_service.ingest(content)
        
        # Validação automática (fail-fast)
        if not questions:
            raise ValueError("Nenhuma pergunta detectada na trilha")
        
        # Salvar perguntas
        template = Template.create(name=file.filename, cycle=cycle)
        for question in questions:
            db.add(QuestionField(
                template_id=template.id,
                field_id=question.field_id,
                sheet_index=question.sheet_index,
                order_index_global=question.order_index_global,
                order_index_sheet=question.order_index_sheet,
                section_name=question.section_name,
                question_text=question.question_text,
                answer_cell_range=question.answer_cell_range,
                inferred_type=question.inferred_type,
                required=True,  # OBRIGATÓRIO
            ))
        
        db.commit()
        
        return {
            "status": "✅ Trilha educacional ingerida",
            "template_id": template.id,
            "questions_count": len(questions),
            "sheets_analyzed": audit_report["step_2_questions"]["sheets_analyzed"],
            "audit": audit_report,
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao ingerir trilha: {str(e)}"
        )
```

### Mudanças Específicas

| Antes | Depois | Motivo |
|-------|--------|--------|
| `FillableAreaDetector` | `TrailIngestionService` | Semântica formal |
| `candidates = detector.detect()` | `questions, audit = service.ingest()` | Fail-fast |
| `FillableFieldCandidate` | `QuestionField` | Modelo novo |
| Sem validação | Com fail-fast | Garantia de qualidade |
| Sem `sheet_index` | Com `sheet_index` | Ordem preservada |
| Sem `order_index_global` | Com `order_index_global` | Sequência absoluta |

---

## ✅ PASSO 2: Criar Modelo QuestionField (30 min)

**Arquivo**: `backend/app/models/question_field.py` (NOVO)

```python
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class QuestionField(Base):
    __tablename__ = "question_fields"
    
    # PK
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    
    # 🔑 Identificação
    field_id = Column(String(16), unique=True, nullable=False, index=True)
    
    # 📍 Ordem (CRÍTICO)
    sheet_index = Column(Integer, nullable=False)  # 0, 1, 2...
    order_index_sheet = Column(Integer, nullable=False)  # 1, 2, 3 dentro da aba
    order_index_global = Column(Integer, nullable=False, index=True)  # 1, 2, 3 na trilha
    
    # 🏷️ Contexto
    section_name = Column(String(255), nullable=True)
    section_index = Column(Integer, nullable=True)
    
    # ❓ Pergunta
    question_text = Column(Text, nullable=False)
    
    # 💾 Resposta
    answer_cell_range = Column(String(50), nullable=True)  # "B2:D4"
    answer_row_start = Column(Integer, nullable=True)
    answer_row_end = Column(Integer, nullable=True)
    
    # 📋 Semântica
    inferred_type = Column(String(50), default="text_long")  # text_short | text_long | number
    validation_type = Column(String(50), nullable=True)
    example_value = Column(Text, nullable=True)
    
    # ⚙️ Metadados
    required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    template = relationship("Template", back_populates="questions")
    
    # Índices para performance
    __table_args__ = (
        Index('ix_template_order', 'template_id', 'order_index_global'),
        Index('ix_field_id', 'field_id'),
    )
```

**Registrar em models/__init__.py**:
```python
from backend.app.models.question_field import QuestionField
```

---

## ✅ PASSO 3: Adicionar Colunas ao BD (30 min)

**Arquivo**: `backend/alembic/versions/add_trail_columns.py` (NOVO)

```python
"""Add trail columns to fillable_fields

Revision ID: 003
Revises: 002
Create Date: 2026-01-18

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Renomear tabela antiga (compatibilidade)
    op.execute("ALTER TABLE fillable_fields RENAME TO fillable_fields_legacy")
    
    # Criar tabela nova com colunas de ordem
    op.create_table(
        'fillable_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.String(16), nullable=False, unique=True),
        sa.Column('sheet_index', sa.Integer(), nullable=False),
        sa.Column('order_index_sheet', sa.Integer(), nullable=False),
        sa.Column('order_index_global', sa.Integer(), nullable=False),
        sa.Column('section_name', sa.String(255), nullable=True),
        sa.Column('section_index', sa.Integer(), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('answer_cell_range', sa.String(50), nullable=True),
        sa.Column('inferred_type', sa.String(50), default='text_long'),
        sa.Column('required', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Índices
    op.create_index('ix_order_global', 'fillable_fields', ['template_id', 'order_index_global'])
    op.create_index('ix_field_id', 'fillable_fields', ['field_id'])

def downgrade():
    op.drop_table('fillable_fields')
    op.execute("ALTER TABLE fillable_fields_legacy RENAME TO fillable_fields")
```

**Executar migration**:
```bash
cd backend
alembic upgrade head
```

---

## ✅ PASSO 4: Criar Endpoints de Trilha (1h)

**Arquivo**: `backend/routers/trail_endpoints.py` (NOVO)

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.app.models import QuestionField, Template

router = APIRouter(prefix="/api/v1/trails", tags=["trails"])

@router.get("/templates/{template_id}/trail")
async def get_template_trail(template_id: int, db: Session = Depends(get_db)):
    """
    Retorna a trilha educacional completa de um template
    
    Response:
    {
        "template_id": 1,
        "questions": [
            {
                "field_id": "abc123def",
                "order_index_global": 0,
                "question_text": "Qual é seu mercado-alvo?",
                "sheet_name": "Diagnóstico",
                "section_name": "Mercado",
                "required": true,
                "status": "not_answered"  # ou "answered" se já tem resposta
            },
            ...
        ]
    }
    """
    template = db.query(Template).filter_by(id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    questions = db.query(QuestionField).filter_by(
        template_id=template_id
    ).order_by(QuestionField.order_index_global).all()
    
    return {
        "template_id": template_id,
        "total_questions": len(questions),
        "questions": [
            {
                "field_id": q.field_id,
                "order_index_global": q.order_index_global,
                "order_index_sheet": q.order_index_sheet,
                "question_text": q.question_text,
                "section_name": q.section_name,
                "required": q.required,
                "inferred_type": q.inferred_type,
            }
            for q in questions
        ]
    }

@router.post("/templates/{template_id}/answer/{field_id}")
async def submit_answer(
    template_id: int,
    field_id: str,
    answer_data: dict,
    db: Session = Depends(get_db)
):
    """
    Submete resposta a uma pergunta
    
    Body:
    {
        "answer": "texto da resposta...",
        "founder_id": 123
    }
    """
    question = db.query(QuestionField).filter_by(
        template_id=template_id,
        field_id=field_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Pergunta não encontrada")
    
    # Validar sequência (não pode responder pergunta fora de ordem)
    previous_unanswered = db.query(QuestionField).filter(
        QuestionField.template_id == template_id,
        QuestionField.order_index_global < question.order_index_global,
        # ... sem resposta anterior
    ).first()
    
    if previous_unanswered:
        raise HTTPException(
            status_code=400,
            detail=f"Responda a pergunta anterior primeiro"
        )
    
    # Salvar resposta
    db.add(FounderAnswer(
        founder_id=answer_data["founder_id"],
        question_id=question.id,
        answer=answer_data["answer"],
    ))
    db.commit()
    
    return {"status": "✅ Resposta salva", "field_id": field_id}

@router.get("/templates/{template_id}/progress")
async def get_progress(template_id: int, founder_id: int, db: Session = Depends(get_db)):
    """
    Retorna progresso do founder na trilha
    
    Response:
    {
        "progress_percent": 40,
        "answered": 2,
        "total": 5,
        "next_question": {...}
    }
    """
    questions = db.query(QuestionField).filter_by(
        template_id=template_id
    ).order_by(QuestionField.order_index_global).all()
    
    # Contar respostas
    answers = db.query(FounderAnswer).filter_by(founder_id=founder_id)
    answered_count = answers.count()
    
    # Próxima pergunta
    next_question = db.query(QuestionField).filter(
        QuestionField.template_id == template_id,
        ~db.exists().where(
            (FounderAnswer.question_id == QuestionField.id) &
            (FounderAnswer.founder_id == founder_id)
        )
    ).order_by(QuestionField.order_index_global).first()
    
    return {
        "progress_percent": int((answered_count / len(questions)) * 100) if questions else 0,
        "answered": answered_count,
        "total": len(questions),
        "next_question": {
            "field_id": next_question.field_id,
            "question_text": next_question.question_text,
        } if next_question else None,
    }
```

**Registrar em main.py**:
```python
from backend.routers import trail_endpoints

app.include_router(trail_endpoints.router)
```

---

## ✅ PASSO 5: Atualizar Frontend (2-3h)

**Arquivo**: `frontend/components/TemplateTrail.jsx` (NOVO)

```jsx
import React, { useState, useEffect } from 'react';

export function TemplateTrail({ templateId, founderId }) {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [progress, setProgress] = useState(0);
  const [currentQuestion, setCurrentQuestion] = useState(null);

  useEffect(() => {
    // Carregar trilha
    fetch(`/api/v1/trails/templates/${templateId}/trail`)
      .then(r => r.json())
      .then(data => {
        setQuestions(data.questions);
        setCurrentQuestion(data.questions[0]);
      });
    
    // Carregar progresso
    fetch(`/api/v1/trails/templates/${templateId}/progress?founder_id=${founderId}`)
      .then(r => r.json())
      .then(data => setProgress(data.progress_percent));
  }, [templateId, founderId]);

  const handleAnswerSubmit = async (fieldId, answer) => {
    await fetch(`/api/v1/trails/templates/${templateId}/answer/${fieldId}`, {
      method: 'POST',
      body: JSON.stringify({
        answer: answer,
        founder_id: founderId,
      }),
    });
    
    // Avançar para próxima pergunta
    setAnswers(prev => ({ ...prev, [fieldId]: answer }));
    
    // Recarregar progresso
    const res = await fetch(
      `/api/v1/trails/templates/${templateId}/progress?founder_id=${founderId}`
    );
    const data = await res.json();
    setProgress(data.progress_percent);
    setCurrentQuestion(data.next_question);
  };

  return (
    <div className="trail-container">
      {/* Barra de progresso */}
      <div className="progress-bar">
        <div className="progress" style={{ width: `${progress}%` }}>
          {progress}%
        </div>
      </div>
      
      {/* Pergunta atual */}
      {currentQuestion ? (
        <QuestionCard
          question={currentQuestion}
          onSubmit={(answer) => handleAnswerSubmit(currentQuestion.field_id, answer)}
          disabled={false}
        />
      ) : (
        <div className="completed">
          ✅ Trilha completa! Você respondeu todas as perguntas.
        </div>
      )}
      
      {/* Lista de perguntas com status */}
      <div className="questions-list">
        {questions.map((q, i) => (
          <div
            key={q.field_id}
            className={`question-item ${
              answers[q.field_id] ? 'answered' : 'pending'
            }`}
          >
            <span className="order">{i + 1}.</span>
            <span className="text">{q.question_text}</span>
            <span className="status">
              {answers[q.field_id] ? '✅' : '⏳'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## ✅ PASSO 6: Rodar Testes (30 min)

```bash
# Teste de fidelidade
pytest backend/tests/test_trail_fidelity.py -v

# Resultado esperado:
# test_trail_order_sheets_preserved PASSED
# test_trail_order_questions_within_sheet PASSED
# test_trail_no_questions_lost PASSED
# ... (13 total)
# ======================== 13 passed in 0.45s ======================

# Teste E2E (upload → resposta)
pytest backend/tests/test_trail_e2e.py -v
```

---

## ✅ PASSO 7: Validação Final (30 min)

```bash
# 1. Auditoria
python backend/audit_trail_system.py

# Esperado:
# ✓ Snapshot preserva sheet_index
# ✓ Células ordenadas
# ✓ QuestionExtractor funciona
# ✓ TrailIngestionService implementado
# ✓ Cobertura validada

# 2. Testar com template real
curl -X POST http://localhost:8000/api/v1/templates/upload \
  -F "file=@Template_Q1.xlsx" \
  -F "cycle=Q1-2025"

# Esperado:
# {
#   "status": "✅ Trilha educacional ingerida",
#   "questions_count": 5,
#   "audit": {...}
# }

# 3. Obter trilha
curl http://localhost:8000/api/v1/trails/templates/1/trail

# Esperado:
# {
#   "questions": [
#     {"order_index_global": 0, "question_text": "..."},
#     {"order_index_global": 1, "question_text": "..."},
#     ...
#   ]
# }
```

---

## 🔍 Checklist de Integração

- [ ] admin_templates.py atualizado com TrailIngestionService
- [ ] QuestionField model criado
- [ ] Migration do BD executada
- [ ] Endpoints de trilha criados
- [ ] Frontend renderiza perguntas em ordem
- [ ] Frontend bloqueia respostas fora de ordem
- [ ] Barra de progresso funciona
- [ ] Testes passam (13/13)
- [ ] Auditoria aprovada
- [ ] Teste com template real bem-sucedido

---

## 🚨 Troubleshooting

### Erro: "Aba sem perguntas"
**Causa**: Template não tem seção com palavra-chave de pergunta  
**Solução**: Adicionar "Qual", "Descreva" ou palavra-chave em QUESTION_KEYWORDS

### Erro: "order_index_global quebrada"
**Causa**: Perguntas foram extraídas fora de ordem  
**Solução**: Verificar se snapshot está ordenando células corretamente

### Erro: "field_id não é único"
**Causa**: Duas perguntas idênticas com mesmo hash  
**Solução**: Adicionar contexto de row/column ao hash

### Progresso não avança
**Causa**: Resposta não foi salva corretamente  
**Solução**: Verificar FounderAnswer table, validar resposta não nula

---

**Tempo Total de Implementação**: 6-7 horas  
**Complexidade**: Média  
**Status**: Pronto para integração  
