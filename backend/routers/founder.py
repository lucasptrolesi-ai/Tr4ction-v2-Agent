from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
import os

from core.models import SuccessResponse
from db.database import get_db
from db.models import Trail, StepSchema, StepAnswer, UserProgress
from services.xlsx_exporter import generate_xlsx
from services.auth import get_current_user_id, get_current_user, get_current_founder
from db.models import User

router = APIRouter(prefix="/founder")


def get_default_trails():
    """Retorna trilhas padrão para seeding inicial"""
    return [
        {
            "id": "q1-marketing",
            "name": "Marketing Q1",
            "description": "Template completo de marketing para o primeiro trimestre",
            "steps": [
                {"id": "icp", "name": "ICP", "order": 1},
                {"id": "persona", "name": "Persona", "order": 2},
                {"id": "swot", "name": "SWOT", "order": 3},
                {"id": "funil", "name": "Funil de Vendas", "order": 4},
                {"id": "metricas", "name": "Métricas", "order": 5}
            ]
        }
    ]


def seed_default_data(db: Session):
    """Insere dados padrão se o banco estiver vazio"""
    existing = db.query(Trail).first()
    if existing:
        return  # Já tem dados
    
    for trail_data in get_default_trails():
        trail = Trail(
            id=trail_data["id"],
            name=trail_data["name"],
            description=trail_data["description"],
            status="active"
        )
        db.add(trail)
        db.flush()
        
        for step_data in trail_data["steps"]:
            step = StepSchema(
                trail_id=trail.id,
                step_id=step_data["id"],
                step_name=step_data["name"],
                order=step_data["order"],
                schema={
                    "fields": [
                        {
                            "name": f"{step_data['id']}_campo1",
                            "type": "text",
                            "label": f"Campo Principal - {step_data['name']}",
                            "required": True
                        },
                        {
                            "name": f"{step_data['id']}_descricao",
                            "type": "textarea",
                            "label": "Descrição detalhada",
                            "required": False
                        }
                    ]
                }
            )
            db.add(step)
    
    db.commit()


@router.get("/trails")
async def list_trails(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """
    Lista todas as trilhas disponíveis para o founder com progresso
    """
    try:
        # Seed dados padrão se necessário
        seed_default_data(db)
        
        # Busca trilhas do banco
        trails = db.query(Trail).filter(Trail.status == "active").all()
        
        result = []
        for trail in trails:
            # Busca steps dessa trilha
            steps = db.query(StepSchema).filter(
                StepSchema.trail_id == trail.id
            ).order_by(StepSchema.order).all()
            
            steps_with_progress = []
            for idx, step in enumerate(steps):
                # Busca progresso salvo
                progress = db.query(UserProgress).filter(
                    UserProgress.user_id == user_id,
                    UserProgress.trail_id == trail.id,
                    UserProgress.step_id == step.step_id
                ).first()
                
                # Busca respostas salvas
                answer = db.query(StepAnswer).filter(
                    StepAnswer.user_id == user_id,
                    StepAnswer.trail_id == trail.id,
                    StepAnswer.step_id == step.step_id
                ).first()
                
                # Calcula progresso baseado nas respostas
                calc_progress = 0
                if answer and answer.answers:
                    calc_progress = min(100, len(answer.answers) * 25)
                
                is_locked = progress.is_locked if progress else (idx > 0)  # Primeiro desbloqueado
                is_completed = progress.is_completed if progress else False
                
                steps_with_progress.append({
                    "id": step.step_id,
                    "name": step.step_name,
                    "locked": is_locked,
                    "completed": is_completed,
                    "progress": progress.progress_percent if progress else calc_progress
                })
            
            result.append({
                "id": trail.id,
                "name": trail.name,
                "description": trail.description or "",
                "steps": steps_with_progress
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trails/{trail_id}/steps/{step_id}/schema")
async def get_step_schema(trail_id: str, step_id: str, db: Session = Depends(get_db)):
    """
    Retorna o schema de campos de uma etapa específica
    """
    try:
        step = db.query(StepSchema).filter(
            StepSchema.trail_id == trail_id,
            StepSchema.step_id == step_id
        ).first()
        
        if not step:
            raise HTTPException(status_code=404, detail=f"Step {step_id} not found in trail {trail_id}")
        
        return {
            "trail_id": trail_id,
            "step_id": step_id,
            "step_name": step.step_name,
            "fields": step.schema.get("fields", []) if step.schema else []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trails/{trail_id}/steps/{step_id}/progress")
async def get_step_progress(trail_id: str, step_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """
    Retorna o progresso atual de uma etapa específica
    """
    try:
        
        # Busca progresso
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.trail_id == trail_id,
            UserProgress.step_id == step_id
        ).first()
        
        # Busca respostas salvas
        answer = db.query(StepAnswer).filter(
            StepAnswer.user_id == user_id,
            StepAnswer.trail_id == trail_id,
            StepAnswer.step_id == step_id
        ).first()
        
        return {
            "trail_id": trail_id,
            "step_id": step_id,
            "isLocked": progress.is_locked if progress else False,
            "formData": answer.answers if answer else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SaveProgressBody(BaseModel):
    formData: dict


@router.post("/trails/{trail_id}/steps/{step_id}/progress")
async def save_step_progress(trail_id: str, step_id: str, body: SaveProgressBody, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """
    Salva o progresso de preenchimento de uma etapa
    """
    try:
        
        # Busca ou cria StepAnswer
        answer = db.query(StepAnswer).filter(
            StepAnswer.user_id == user_id,
            StepAnswer.trail_id == trail_id,
            StepAnswer.step_id == step_id
        ).first()
        
        if answer:
            answer.answers = body.formData
            answer.updated_at = datetime.utcnow()
        else:
            answer = StepAnswer(
                trail_id=trail_id,
                step_id=step_id,
                user_id=user_id,
                answers=body.formData
            )
            db.add(answer)
        
        # Atualiza progresso
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.trail_id == trail_id,
            UserProgress.step_id == step_id
        ).first()
        
        calc_progress = min(100, len(body.formData) * 25) if body.formData else 0
        
        if progress:
            progress.progress_percent = calc_progress
            progress.is_completed = calc_progress >= 100
            progress.updated_at = datetime.utcnow()
        else:
            progress = UserProgress(
                user_id=user_id,
                trail_id=trail_id,
                step_id=step_id,
                is_locked=False,
                is_completed=calc_progress >= 100,
                progress_percent=calc_progress
            )
            db.add(progress)
        
        db.commit()
        
        return SuccessResponse(data={
            "trail_id": trail_id,
            "step_id": step_id,
            "saved": True,
            "progress": calc_progress,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trails/{trail_id}/download")
async def download_trail(trail_id: str, db: Session = Depends(get_db)):
    """
    Gera e retorna o Excel preenchido com os dados do founder (LEGADO)
    Redireciona para o novo endpoint de export
    """
    return await export_trail_xlsx(trail_id, db)


@router.get("/trails/{trail_id}/export/xlsx")
async def export_trail_xlsx(trail_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """
    Gera e retorna o Excel (XLSX) preenchido com os dados do founder.
    Streaming response - não grava arquivo em disco.
    """
    try:
        # Busca a trilha
        trail = db.query(Trail).filter(Trail.id == trail_id).first()
        if not trail:
            raise HTTPException(status_code=404, detail="Trilha não encontrada")
        
        # Busca os steps ordenados
        steps = (
            db.query(StepSchema)
            .filter(StepSchema.trail_id == trail_id)
            .order_by(StepSchema.order)
            .all()
        )
        
        answers = db.query(StepAnswer).filter(
            StepAnswer.trail_id == trail_id,
            StepAnswer.user_id == user_id
        ).all()
        
        # Organiza respostas por step_id
        answers_by_step = {a.step_id: a.answers for a in answers}
        
        # Gera o XLSX
        stream = generate_xlsx(trail, steps, answers_by_step)
        
        # Retorna como streaming response
        filename = f"{trail_id}_preenchido.xlsx"
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
