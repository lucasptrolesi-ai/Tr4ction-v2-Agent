"""
Trail Endpoints - Trilhas Educacionais com Sequência Garantida

RESPONSABILIDADE:
- GET /trails/{template_id}/trail - Retorna trilha completa
- POST /trails/{template_id}/answer/{field_id} - Submete resposta com validação
- GET /trails/{template_id}/progress - Progresso do founder
- GET /trails/{template_id}/next-question - Próxima pergunta válida

GARANTIAS:
✅ Backend é fonte única da ordem
✅ Validação de sequência SEMPRE no backend
✅ Nenhum bypass possível via frontend
✅ Ordem preservada em refresh de página
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from db.database import get_db
from db.models import User, StepAnswer
from app.models.template_definition import TemplateDefinition, FillableField
from services.auth import get_current_user

router = APIRouter(prefix="/api/v1/trails", tags=["trails"])
logger = logging.getLogger(__name__)


def get_next_unanswered_question(
    template_id: str,
    founder_id: str,
    db: Session,
) -> Optional[Dict[str, Any]]:
    """
    ✅ AJUSTE 3: Backend como única fonte da ordem
    
    Retorna a próxima pergunta não respondida em ordem de sequência.
    Usa backend como autoridade absoluta.
    
    Args:
        template_id: ID do template
        founder_id: ID do founder
        db: Sessão do banco
    
    Returns:
        Próxima pergunta ou None se completou trilha
    """
    # 1. Buscar todas as perguntas em ordem
    questions = db.query(FillableField).filter_by(
        template_id=template_id
    ).order_by(FillableField.order_index.asc()).all()
    
    if not questions:
        return None
    
    # 2. Verificar qual é a próxima não respondida
    for question in questions:
        # Buscar se founder respondeu essa pergunta
        answer = db.query(StepAnswer).filter(
            and_(
                StepAnswer.user_id == founder_id,
                StepAnswer.step_id == question.field_id,  # field_id mapeia para step_id
            )
        ).first()
        
        if not answer:
            # Encontrou uma não respondida
            return {
                "id": question.id,
                "field_id": question.field_id,
                "template_id": template_id,
                "sheet_name": question.sheet_name,
                "cell_range": question.cell_range,
                "label": question.label,
                "inferred_type": question.inferred_type,
                "required": question.required,
                "example_value": question.example_value,
                "order_index": question.order_index,
            }
    
    # Todas respondidas
    return None


def validate_sequence(
    template_id: str,
    field_id: str,
    founder_id: str,
    db: Session,
) -> tuple[bool, Optional[str]]:
    """
    ✅ AJUSTE 2: Validação de sequência obrigatória
    
    Verifica se founder pode responder essa pergunta.
    Precisa ter respondido TODAS as anteriores.
    
    Args:
        template_id: ID do template
        field_id: ID do campo
        founder_id: ID do founder
        db: Sessão do banco
    
    Returns:
        (é_válido, mensagem_erro_ou_none)
    """
    # 1. Buscar a pergunta
    question = db.query(FillableField).filter(
        and_(
            FillableField.template_id == template_id,
            FillableField.field_id == field_id,
        )
    ).first()
    
    if not question:
        return False, "Pergunta não encontrada"
    
    # 2. Buscar todas as perguntas anteriores (ordem menor)
    previous_questions = db.query(FillableField).filter(
        and_(
            FillableField.template_id == template_id,
            FillableField.order_index < question.order_index,
        )
    ).order_by(FillableField.order_index.asc()).all()
    
    # 3. Verificar se todas foram respondidas
    for prev_q in previous_questions:
        answer = db.query(StepAnswer).filter(
            and_(
                StepAnswer.user_id == founder_id,
                StepAnswer.step_id == prev_q.field_id,
            )
        ).first()
        
        if not answer:
            return False, (
                f"Você precisa responder as perguntas anteriores. "
                f"Respondidas: {len([q for q in previous_questions if db.query(StepAnswer).filter(and_(StepAnswer.user_id == founder_id, StepAnswer.step_id == q.field_id)).first()])}/"
                f"{len(previous_questions)}"
            )
    
    return True, None


@router.get("/templates/{template_id}/trail")
async def get_template_trail(
    template_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    ✅ Retorna a trilha educacional completa de um template
    
    Resposta:
    ```json
    {
        "template_id": "abc123",
        "total_questions": 5,
        "questions": [
            {
                "field_id": "q1",
                "order_index": 0,
                "label": "Qual é o desafio?",
                "inferred_type": "text_long",
                "required": true
            },
            ...
        ]
    }
    ```
    """
    # Verificar template existe
    template = db.query(TemplateDefinition).filter_by(id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    # Buscar perguntas em ordem
    questions = db.query(FillableField).filter_by(
        template_id=template_id
    ).order_by(FillableField.order_index.asc()).all()
    
    return {
        "template_id": template_id,
        "template_key": template.template_key,
        "cycle": template.cycle,
        "total_questions": len(questions),
        "questions": [
            {
                "id": q.id,
                "field_id": q.field_id,
                "sheet_name": q.sheet_name,
                "cell_range": q.cell_range,
                "label": q.label,
                "inferred_type": q.inferred_type,
                "required": q.required,
                "order_index": q.order_index,
                "example_value": q.example_value,
            }
            for q in questions
        ]
    }


@router.get("/templates/{template_id}/next-question")
async def get_next_question(
    template_id: str,
    founder_id: str = Query(..., description="ID do founder"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    ✅ AJUSTE 3: Backend retorna próxima pergunta válida
    
    Frontend nunca calcula isto localmente.
    Backend é a autoridade absoluta da sequência.
    
    Response:
    ```json
    {
        "has_next": true,
        "question": {...},
        "progress_percent": 40,
        "answered_count": 2,
        "total_count": 5
    }
    ```
    """
    # Verificar template existe
    template = db.query(TemplateDefinition).filter_by(id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    # Buscar próxima pergunta
    next_question = get_next_unanswered_question(template_id, founder_id, db)
    
    # Contar progresso
    total_questions = db.query(FillableField).filter_by(template_id=template_id).count()
    answered = db.query(StepAnswer).filter_by(user_id=founder_id).count()
    
    return {
        "has_next": next_question is not None,
        "question": next_question,
        "progress_percent": int((answered / total_questions) * 100) if total_questions > 0 else 0,
        "answered_count": answered,
        "total_count": total_questions,
    }


@router.post("/templates/{template_id}/answer/{field_id}")
async def submit_answer(
    template_id: str,
    field_id: str,
    answer_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    ✅ AJUSTE 2 + 3: Submete resposta com validação de sequência no backend
    
    CRÍTICO: Essa validação SEMPRE acontece aqui.
    Frontend não pode fazer bypass.
    
    Request:
    ```json
    {
        "answer": "Minha resposta é...",
        "context": "opcional"
    }
    ```
    
    Response:
    ```json
    {
        "status": "✅ Resposta salva",
        "field_id": "q1",
        "next_question": {...}
    }
    ```
    
    Errors:
    - 400: Sequência violada
    - 404: Pergunta não encontrada
    - 422: Resposta inválida
    """
    try:
        # 1. Validar pergunta existe
        question = db.query(FillableField).filter(
            and_(
                FillableField.template_id == template_id,
                FillableField.field_id == field_id,
            )
        ).first()
        
        if not question:
            raise HTTPException(status_code=404, detail="Pergunta não encontrada")
        
        # 2. ✅ VALIDAR SEQUÊNCIA - Isso é obrigatório
        is_valid, error_msg = validate_sequence(
            template_id, field_id, current_user.id, db
        )
        
        if not is_valid:
            # Bloquear qualquer tentativa de bypass
            logger.warning(
                f"⚠️ TENTATIVA DE BYPASS DETECTADA: "
                f"user={current_user.id}, field_id={field_id}, "
                f"template_id={template_id}, reason={error_msg}"
            )
            raise HTTPException(
                status_code=400,
                detail=error_msg or "Você precisa responder as perguntas anteriores"
            )
        
        # 3. Validar resposta não vazia
        answer_text = answer_data.get("answer", "").strip()
        if not answer_text and question.required:
            raise HTTPException(
                status_code=422,
                detail="Resposta obrigatória não pode estar vazia"
            )
        
        # 4. Salvar resposta
        # Mapear para StepAnswer
        step_answer = db.query(StepAnswer).filter(
            and_(
                StepAnswer.user_id == current_user.id,
                StepAnswer.step_id == field_id,
            )
        ).first()
        
        if step_answer:
            # Atualizar
            step_answer.answers[field_id] = answer_text
            step_answer.updated_at = datetime.utcnow()
        else:
            # Criar novo
            step_answer = StepAnswer(
                trail_id=template_id,
                step_id=field_id,
                user_id=current_user.id,
                answers={field_id: answer_text},
            )
            db.add(step_answer)
        
        db.commit()
        
        logger.info(
            f"✅ Resposta salva: "
            f"user={current_user.id}, field_id={field_id}, template_id={template_id}"
        )
        
        # 5. Retornar próxima pergunta
        next_question = get_next_unanswered_question(template_id, current_user.id, db)
        
        return {
            "status": "✅ Resposta salva",
            "field_id": field_id,
            "next_question": next_question,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao salvar resposta: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao salvar resposta")


@router.get("/templates/{template_id}/progress")
async def get_progress(
    template_id: str,
    founder_id: str = Query(..., description="ID do founder"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    ✅ AJUSTE 3: Progresso baseado 100% no backend
    
    Frontend obtém estado completo do backend sempre.
    Em refresh de página, estado é recuperado corretamente.
    
    Response:
    ```json
    {
        "progress_percent": 40,
        "answered": 2,
        "total": 5,
        "next_question": {...},
        "is_complete": false
    }
    ```
    """
    # Verificar template
    template = db.query(TemplateDefinition).filter_by(id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    # Contar respostas
    all_questions = db.query(FillableField).filter_by(
        template_id=template_id
    ).order_by(FillableField.order_index.asc()).all()
    
    answered_count = 0
    for question in all_questions:
        answer = db.query(StepAnswer).filter(
            and_(
                StepAnswer.user_id == founder_id,
                StepAnswer.step_id == question.field_id,
            )
        ).first()
        if answer:
            answered_count += 1
    
    total_count = len(all_questions)
    is_complete = answered_count == total_count and total_count > 0
    
    # Próxima pergunta
    next_question = get_next_unanswered_question(template_id, founder_id, db)
    
    return {
        "progress_percent": int((answered_count / total_count) * 100) if total_count > 0 else 0,
        "answered": answered_count,
        "total": total_count,
        "next_question": next_question,
        "is_complete": is_complete,
    }
