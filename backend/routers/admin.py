from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

from usecases.admin_usecase import (
    list_knowledge_docs,
    remove_knowledge_doc,
    reset_vector_db,
)
from usecases.admin_templates_usecase import (
    upload_and_ingest_template,
    list_templates_by_cycle,
    get_template_by_key,
    update_template_status,
    list_available_cycles,
)
from core.models import SuccessResponse, ErrorResponse
from db.database import get_db
from db.models import Trail, StepSchema, StepAnswer, UserProgress, User
from services.xlsx_exporter import generate_xlsx
from services.xlsx_parser import parse_template_xlsx
from services.auth import get_current_admin, get_current_user_id

router = APIRouter(prefix="/admin")


class DeleteBody(BaseModel):
    doc_id: str


@router.get("/knowledge", response_model=SuccessResponse)
async def list_knowledge(
    current_admin: User = Depends(get_current_admin)
):
    """Lista documentos da base de conhecimento (apenas admin)"""
    try:
        data = list_knowledge_docs()
        return SuccessResponse(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/knowledge",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse}},
)
async def remove_doc(
    body: DeleteBody,
    current_admin: User = Depends(get_current_admin)
):
    """Remove documento da base de conhecimento (apenas admin)"""
    try:
        data = remove_knowledge_doc(body.doc_id)
        return SuccessResponse(data=data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-vector-db", response_model=SuccessResponse)
async def reset_db(
    current_admin: User = Depends(get_current_admin)
):
    """⚠️ PERIGOSO: Reseta todo o banco vetorial (apenas admin)"""
    try:
        data = reset_vector_db()
        return SuccessResponse(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# Endpoints de Templates e Trilhas
# ======================================================

@router.get("/trails")
async def list_admin_trails(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Lista todas as trilhas disponíveis para administração (apenas admin)
    """
    try:
        trails = db.query(Trail).all()
        
        result = []
        for trail in trails:
            steps_count = db.query(StepSchema).filter(
                StepSchema.trail_id == trail.id
            ).count()
            
            result.append({
                "id": trail.id,
                "name": trail.name,
                "description": trail.description or "",
                "steps_count": steps_count,
                "created_at": trail.created_at.isoformat() if trail.created_at else None,
                "status": trail.status
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateTrailBody(BaseModel):
    id: str
    name: str
    description: str = ""


@router.post("/trails")
async def create_trail(
    body: CreateTrailBody,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Cria uma nova trilha (apenas admin)
    """
    try:
        existing = db.query(Trail).filter(Trail.id == body.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Trilha já existe com esse ID")
        
        trail = Trail(
            id=body.id,
            name=body.name,
            description=body.description,
            status="draft"
        )
        db.add(trail)
        db.commit()
        
        return SuccessResponse(data={
            "id": trail.id,
            "name": trail.name,
            "created": True
        })
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class UploadTemplateBody(BaseModel):
    template_data: list
    file_name: str
    sheet_name: str


@router.post("/trails/{trail_id}/upload-template", response_model=SuccessResponse)
async def upload_template(
    trail_id: str,
    body: UploadTemplateBody,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Recebe dados do Excel parseado e salva o schema da trilha (apenas admin)
    """
    try:
        # Verifica se trilha existe
        trail = db.query(Trail).filter(Trail.id == trail_id).first()
        if not trail:
            raise HTTPException(status_code=404, detail="Trilha não encontrada")
        
        # Remove steps antigos
        db.query(StepSchema).filter(StepSchema.trail_id == trail_id).delete()
        
        # Cria novos steps a partir do template
        for idx, field_data in enumerate(body.template_data):
            step = StepSchema(
                trail_id=trail_id,
                step_id=f"step-{idx+1}",
                step_name=field_data.get("name", f"Etapa {idx+1}"),
                order=idx,
                schema={
                    "fields": [field_data] if isinstance(field_data, dict) else field_data
                }
            )
            db.add(step)
        
        db.commit()
        
        return SuccessResponse(data={
            "trail_id": trail_id,
            "file_name": body.file_name,
            "sheet_name": body.sheet_name,
            "fields_detected": len(body.template_data),
            "status": "processed"
        })
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trails/{trail_id}/upload-xlsx")
async def upload_xlsx_template(
    trail_id: str,
    file: UploadFile = File(...),
    replace_existing: bool = True,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Faz upload de um arquivo Excel e gera schemas automaticamente (apenas admin).
    Cada aba do Excel vira uma etapa (step) com seus campos.
    
    Args:
        trail_id: ID da trilha
        file: Arquivo XLSX
        replace_existing: Se True, substitui steps existentes
    """
    try:
        # Valida extensão
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Arquivo deve ser .xlsx ou .xls")
        
        # Verifica se trilha existe, se não, cria
        trail = db.query(Trail).filter(Trail.id == trail_id).first()
        if not trail:
            trail = Trail(
                id=trail_id,
                name=trail_id.replace("-", " ").replace("_", " ").title(),
                description=f"Trilha criada via upload: {file.filename}",
                status="draft"
            )
            db.add(trail)
            db.flush()
        
        # Lê o arquivo
        contents = await file.read()
        
        # Parseia o Excel
        steps_data = parse_template_xlsx(contents)
        
        if not steps_data:
            raise HTTPException(
                status_code=400, 
                detail="Nenhum campo encontrado no Excel. Verifique se o arquivo tem abas com dados na coluna A."
            )
        
        # Remove steps antigos se solicitado
        if replace_existing:
            db.query(StepSchema).filter(StepSchema.trail_id == trail_id).delete()
        
        # Cria novos steps
        steps_created = []
        for step_data in steps_data:
            step = StepSchema(
                trail_id=trail_id,
                step_id=step_data["step_id"],
                step_name=step_data["step_name"],
                order=step_data["order"],
                schema=step_data["schema"]
            )
            db.add(step)
            steps_created.append({
                "step_id": step_data["step_id"],
                "step_name": step_data["step_name"],
                "fields_count": len(step_data["schema"].get("fields", []))
            })
        
        # Atualiza status da trilha
        trail.status = "active"
        trail.updated_at = datetime.utcnow()
        
        db.commit()
        
        return SuccessResponse(data={
            "trail_id": trail_id,
            "file_name": file.filename,
            "steps_created": len(steps_created),
            "steps": steps_created,
            "status": "processed"
        })
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao processar Excel: {str(e)}")


@router.get("/trails/{trail_id}/steps/{step_id}/schema")
async def get_step_schema(trail_id: str, step_id: str, db: Session = Depends(get_db)):
    """
    Retorna o schema de uma etapa específica
    """
    try:
        step = db.query(StepSchema).filter(
            StepSchema.trail_id == trail_id,
            StepSchema.step_id == step_id
        ).first()
        
        if not step:
            # Retorna schema padrão se não encontrar
            return {
                "step_id": step_id,
                "step_name": step_id.upper().replace("-", " "),
                "description": f"Preencha os campos desta etapa: {step_id}",
                "fields": [
                    {
                        "name": f"{step_id}_field_1",
                        "type": "text",
                        "label": "Campo de Exemplo 1",
                        "placeholder": "Digite aqui...",
                        "required": True,
                        "help": "Este é um campo de exemplo"
                    },
                    {
                        "name": f"{step_id}_field_2",
                        "type": "textarea",
                        "label": "Descrição Detalhada",
                        "placeholder": "Descreva com detalhes...",
                        "required": False,
                        "help": "Quanto mais detalhado, melhor!"
                    }
                ]
            }
        
        return {
            "step_id": step.step_id,
            "step_name": step.step_name,
            "description": step.description or f"Preencha os campos: {step.step_name}",
            "fields": step.schema.get("fields", []) if step.schema else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdateSchemaBody(BaseModel):
    step_id: str
    step_name: str
    fields: list


@router.put("/trails/{trail_id}/steps/{step_id}/schema")
async def update_step_schema(trail_id: str, step_id: str, body: UpdateSchemaBody, db: Session = Depends(get_db)):
    """
    Atualiza o schema de uma etapa
    """
    try:
        step = db.query(StepSchema).filter(
            StepSchema.trail_id == trail_id,
            StepSchema.step_id == step_id
        ).first()
        
        if step:
            step.step_name = body.step_name
            step.schema = {"fields": body.fields}
            step.updated_at = datetime.utcnow()
        else:
            step = StepSchema(
                trail_id=trail_id,
                step_id=step_id,
                step_name=body.step_name,
                schema={"fields": body.fields}
            )
            db.add(step)
        
        db.commit()
        
        return SuccessResponse(data={
            "trail_id": trail_id,
            "step_id": step_id,
            "updated": True
        })
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/trail/{trail_id}/progress")
async def get_user_progress(user_id: str, trail_id: str, db: Session = Depends(get_db)):
    """
    Retorna o progresso de um founder em uma trilha
    """
    try:
        # Busca steps da trilha
        steps = db.query(StepSchema).filter(
            StepSchema.trail_id == trail_id
        ).order_by(StepSchema.order).all()
        
        steps_data = []
        for idx, step in enumerate(steps):
            progress = db.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.trail_id == trail_id,
                UserProgress.step_id == step.step_id
            ).first()
            
            steps_data.append({
                "id": step.step_id,
                "name": step.step_name,
                "locked": progress.is_locked if progress else (idx > 0),
                "completed": progress.is_completed if progress else False,
                "progress": progress.progress_percent if progress else 0
            })
        
        return {
            "user": {
                "id": user_id,
                "name": f"Founder {user_id}",
                "email": f"{user_id}@example.com"
            },
            "steps": steps_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LockStepBody(BaseModel):
    locked: bool


@router.post("/users/{user_id}/trail/{trail_id}/steps/{step_id}/lock")
async def toggle_step_lock(user_id: str, trail_id: str, step_id: str, body: LockStepBody, db: Session = Depends(get_db)):
    """
    Bloqueia ou desbloqueia uma etapa para um founder
    """
    try:
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.trail_id == trail_id,
            UserProgress.step_id == step_id
        ).first()
        
        if progress:
            progress.is_locked = body.locked
            progress.updated_at = datetime.utcnow()
        else:
            progress = UserProgress(
                user_id=user_id,
                trail_id=trail_id,
                step_id=step_id,
                is_locked=body.locked,
                is_completed=False,
                progress_percent=0
            )
            db.add(progress)
        
        db.commit()
        
        return SuccessResponse(data={
            "user_id": user_id,
            "trail_id": trail_id,
            "step_id": step_id,
            "locked": body.locked,
            "updated": True
        })
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/trails/{trail_id}/export/xlsx")
async def export_user_trail_xlsx(
    user_id: str,
    trail_id: str,
    db: Session = Depends(get_db)
):
    """
    Exporta o Excel (XLSX) preenchido de um founder específico.
    Para uso do Admin visualizar/baixar dados de um founder.
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
        
        # Busca as respostas do usuário específico
        answers = db.query(StepAnswer).filter(
            StepAnswer.trail_id == trail_id,
            StepAnswer.user_id == user_id
        ).all()
        
        # Organiza respostas por step_id
        answers_by_step = {a.step_id: a.answers for a in answers}
        
        # Gera o XLSX
        stream = generate_xlsx(trail, steps, answers_by_step)
        
        # Retorna como streaming response
        filename = f"{user_id}_{trail_id}.xlsx"
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


# ======================================================
# Endpoints de Dashboard - Progresso dos Founders
# ======================================================

@router.get("/founders/progress")
async def get_founders_progress(db: Session = Depends(get_db)):
    """
    Lista todos os founders com seu progresso em cada trilha.
    Usado no dashboard administrativo.
    """
    try:
        # Busca todos os founders (usuários com role 'founder')
        founders = db.query(User).filter(User.role == "founder", User.is_active == True).all()
        
        # Se não houver founders, retorna lista vazia
        if not founders:
            return []
        
        # Busca todos os progresses e agrupa por user_id
        user_progresses = db.query(UserProgress).all()
        
        # Agrupa progresso por user_id
        progress_by_user = {}
        for progress in user_progresses:
            if progress.user_id not in progress_by_user:
                progress_by_user[progress.user_id] = []
            progress_by_user[progress.user_id].append(progress)
        
        # Busca nomes dos steps
        all_steps = db.query(StepSchema).all()
        step_names = {s.step_id: s.step_name for s in all_steps}
        
        # Formata resultado para cada founder
        result = []
        for founder in founders:
            user_id = founder.id
            user_progress_list = progress_by_user.get(user_id, [])
            
            # Agrupa por trilha
            trails = {}
            total_progress = 0
            step_count = 0
            
            for progress in user_progress_list:
                trail_id = progress.trail_id
                if trail_id not in trails:
                    trails[trail_id] = []
                
                trails[trail_id].append({
                    "id": progress.step_id,
                    "name": step_names.get(progress.step_id, progress.step_id),
                    "progress": progress.progress_percent or 0,
                    "completed": progress.is_completed,
                    "locked": progress.is_locked
                })
                
                total_progress += progress.progress_percent or 0
                step_count += 1
            
            # Calcula progresso médio
            avg_progress = total_progress // step_count if step_count > 0 else 0
            
            # Determina risco baseado no progresso
            risk = "low" if avg_progress >= 60 else "medium" if avg_progress >= 30 else "high"
            
            # Pega a primeira trilha e seus steps
            first_trail_id = list(trails.keys())[0] if trails else None
            steps = trails.get(first_trail_id, []) if first_trail_id else []
            
            # Determina step atual
            current_step = "Não iniciado"
            for step in steps:
                if not step["completed"] and not step["locked"] and step["progress"] > 0:
                    current_step = step["name"]
                    break
                elif step["completed"]:
                    current_step = step["name"] + " ✓"
            
            result.append({
                "id": user_id,
                "name": founder.name or founder.company_name or "Founder",
                "email": founder.email,
                "trailId": first_trail_id,
                "currentStep": current_step,
                "progress": avg_progress,
                "risk": risk,
                "steps": steps
            })
        
        # Ordena por progresso (menor primeiro para ver quem precisa de atenção)
        result.sort(key=lambda x: x["progress"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_user_display_name(user_id: str, db: Session = None) -> str:
    """Retorna um nome amigável para o user_id buscando do banco"""
    if db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user.name or user.company_name or user.email
    
    # Fallback para IDs sem usuário correspondente
    return user_id.replace("-", " ").title()


@router.post("/founders/{user_id}/steps/{step_id}/unlock")
async def unlock_step_for_founder(
    user_id: str, 
    step_id: str, 
    trail_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Desbloqueia uma etapa específica para um founder.
    """
    try:
        # Se trail_id não foi passado, busca a primeira trilha do usuário
        if not trail_id:
            progress = db.query(UserProgress).filter(
                UserProgress.user_id == user_id
            ).first()
            trail_id = progress.trail_id if progress else None
        
        if not trail_id:
            raise HTTPException(status_code=404, detail="Trilha não encontrada para este usuário")
        
        # Busca ou cria o progresso
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.trail_id == trail_id,
            UserProgress.step_id == step_id
        ).first()
        
        if progress:
            progress.is_locked = False
            progress.updated_at = datetime.utcnow()
        else:
            progress = UserProgress(
                user_id=user_id,
                trail_id=trail_id,
                step_id=step_id,
                is_locked=False,
                is_completed=False,
                progress_percent=0
            )
            db.add(progress)
        
        db.commit()
        
        return SuccessResponse(data={
            "user_id": user_id,
            "step_id": step_id,
            "trail_id": trail_id,
            "unlocked": True
        })
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/founders/{user_id}/trails/{trail_id}/answers")
async def get_founder_answers(
    user_id: str,
    trail_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna todas as respostas de um founder em uma trilha específica.
    Usado para revisão pelo admin.
    """
    try:
        # Busca respostas
        answers = db.query(StepAnswer).filter(
            StepAnswer.user_id == user_id,
            StepAnswer.trail_id == trail_id
        ).all()
        
        # Busca steps para ter os nomes
        steps = db.query(StepSchema).filter(
            StepSchema.trail_id == trail_id
        ).order_by(StepSchema.order).all()
        
        step_info = {s.step_id: {"name": s.step_name, "schema": s.schema} for s in steps}
        
        result = []
        for answer in answers:
            info = step_info.get(answer.step_id, {})
            result.append({
                "step_id": answer.step_id,
                "step_name": info.get("name", answer.step_id),
                "answers": answer.answers,
                "schema": info.get("schema", {}),
                "updated_at": answer.updated_at.isoformat() if answer.updated_at else None
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# � MÉTRICAS DO RAG
# ======================================================

@router.get("/rag/metrics")
async def get_rag_metrics_endpoint():
    """
    Retorna métricas agregadas de uso do RAG.
    
    Inclui:
    - Total de queries
    - Queries com/sem contexto
    - Tempo médio de resposta
    - Similaridade média
    - Top queries e documentos
    """
    try:
        from services.rag_metrics import get_rag_metrics
        metrics = get_rag_metrics()
        return SuccessResponse(data=metrics)
    except ImportError:
        raise HTTPException(status_code=501, detail="Serviço de métricas não disponível")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/metrics/history")
async def get_rag_history_endpoint(limit: int = 100):
    """
    Retorna histórico de queries recentes.
    
    Args:
        limit: Número máximo de queries a retornar (default: 100)
    """
    try:
        from services.rag_metrics import get_rag_history
        history = get_rag_history(limit=limit)
        return SuccessResponse(data={
            "queries": history,
            "total": len(history)
        })
    except ImportError:
        raise HTTPException(status_code=501, detail="Serviço de métricas não disponível")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/metrics/daily")
async def get_daily_stats_endpoint(days: int = 30):
    """
    Retorna estatísticas diárias de uso.
    
    Args:
        days: Número de dias a retornar (default: 30)
    """
    try:
        from services.rag_metrics import get_daily_stats
        stats = get_daily_stats(days=days)
        return SuccessResponse(data={
            "stats": stats,
            "days": days
        })
    except ImportError:
        raise HTTPException(status_code=501, detail="Serviço de métricas não disponível")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# �📚 KNOWLEDGE BASE RAG - Upload e Indexação de Documentos
# ======================================================

from services.knowledge_service import (
    index_document,
    search_knowledge,
    get_knowledge_stats,
    get_indexed_documents,
    delete_document as delete_knowledge_doc,
    validate_upload,
    get_supported_formats,
    get_context_for_query
)
import tempfile
import os as os_module
from dataclasses import asdict


@router.get("/knowledge/formats")
async def list_supported_formats():
    """
    Retorna os formatos de arquivo suportados para upload.
    """
    return SuccessResponse(data={
        "formats": get_supported_formats(),
        "description": "Formatos suportados para upload na base de conhecimento"
    })


@router.get("/knowledge/stats")
async def get_kb_stats():
    """
    Retorna estatísticas da base de conhecimento.
    - Total de documentos
    - Total de chunks indexados
    - Informações do storage
    """
    try:
        stats = get_knowledge_stats()
        return SuccessResponse(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/documents")
async def list_kb_documents(
    current_admin: User = Depends(get_current_admin)
):
    """
    Lista todos os documentos indexados na base de conhecimento (apenas admin).
    """
    try:
        docs = get_indexed_documents()
        return SuccessResponse(data={
            "documents": docs,
            "total": len(docs)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi import Form

@router.post("/knowledge/upload")
async def upload_knowledge_document(
    file: UploadFile = File(...),
    trail_id: str = Form(default="geral"),
    step_id: str = Form(default="geral"),
    description: str = Form(default=""),
    version: str = Form(default="1.0"),
    chunk_size: int = Form(default=500),
    chunk_overlap: int = Form(default=50)
):
    """
    Faz upload de um documento para a base de conhecimento COM GOVERNANÇA.
    
    Pipeline:
    1. Valida arquivo (tipo e tamanho)
    2. Extrai texto do documento
    3. Divide em chunks com metadata corporativa
    4. Gera embeddings
    5. Indexa no ChromaDB
    
    Formatos suportados: .pptx, .pdf, .docx, .txt
    
    Metadata Corporativa:
    - trail_id: Trilha associada (ex: "Q1_Marketing", "Q2_Vendas") ou "geral"
    - step_id: Etapa específica (ex: "ICP", "Persona", "SWOT") ou "geral"
    - description: Descrição do material
    - version: Versão do documento (default: "1.0")
    """
    try:
        # Valida arquivo
        contents = await file.read()
        file_size = len(contents)
        
        is_valid, error_msg = validate_upload(file.filename, file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Salva arquivo temporário
        suffix = os_module.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            # Indexa documento com metadata corporativa
            result = index_document(
                file_path=tmp_path,
                filename=file.filename,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                # Metadata corporativa FCJ
                trail_id=trail_id,
                step_id=step_id,
                uploaded_by="admin",  # TODO: pegar do JWT
                version=version,
                description=description
            )
            
            if not result.success:
                raise HTTPException(status_code=400, detail=result.error_message)
            
            return SuccessResponse(data={
                "document_id": result.document_id,
                "filename": result.filename,
                "chunks_indexed": result.chunks_indexed,
                "processing_time_ms": result.processing_time_ms,
                "trail_id": result.trail_id,
                "step_id": result.step_id,
                "status": "indexed"
            })
            
        finally:
            # Remove arquivo temporário
            if os_module.path.exists(tmp_path):
                os_module.remove(tmp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")


@router.delete("/knowledge/documents/{document_id}")
async def delete_kb_document(
    document_id: str,
    current_admin: User = Depends(get_current_admin)
):
    """
    Remove um documento da base de conhecimento (apenas admin).
    Remove tanto os chunks do ChromaDB quanto o arquivo físico.
    """
    try:
        success = delete_knowledge_doc(document_id)
        if success:
            return SuccessResponse(data={
                "document_id": document_id,
                "deleted": True
            })
        else:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/reindex/{document_id}")
async def reindex_kb_document(
    document_id: str,
    current_admin: User = Depends(get_current_admin)
):
    """
    Reindexa um documento específico (apenas admin).
    Útil após atualizações no processador ou nos embeddings.
    """
    try:
        from services.knowledge_service import reindex_document
        result = reindex_document(document_id)
        
        if result.success:
            return SuccessResponse(data={
                "document_id": document_id,
                "reindexed": True,
                "chunks_indexed": result.chunks_indexed,
                "processing_time_ms": result.processing_time_ms
            })
        else:
            raise HTTPException(status_code=400, detail=result.error_message)
    except ImportError:
        raise HTTPException(status_code=501, detail="Funcionalidade de reindexação não disponível")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/reindex-all")
async def reindex_all_documents(
    current_admin: User = Depends(get_current_admin)
):
    """
    ⚠️ OPERAÇÃO PESADA: Reindexa todos os documentos da base de conhecimento (apenas admin).
    Use com cuidado - pode demorar vários minutos e consumir recursos.
    """
    try:
        from services.knowledge_service import reindex_all_documents
        result = reindex_all_documents()
        
        return SuccessResponse(data={
            "total_documents": result.get("total_documents", 0),
            "success_count": result.get("success_count", 0),
            "error_count": result.get("error_count", 0),
            "errors": result.get("errors", []),
            "total_time_ms": result.get("total_time_ms", 0)
        })
    except ImportError:
        raise HTTPException(status_code=501, detail="Funcionalidade de reindexação não disponível")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SearchKnowledgeBody(BaseModel):
    query: str
    n_results: int = 5
    min_similarity: float = 0.3


@router.post("/knowledge/search")
async def search_kb(body: SearchKnowledgeBody):
    """
    Busca semântica na base de conhecimento.
    Retorna documentos relevantes para a query.
    """
    try:
        results = search_knowledge(
            query=body.query,
            n_results=body.n_results,
            min_similarity=body.min_similarity
        )
        
        return SuccessResponse(data={
            "query": body.query,
            "results": results,
            "total": len(results)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TestRAGBody(BaseModel):
    query: str


@router.post("/knowledge/test-rag")
async def test_rag_context(body: TestRAGBody):
    """
    Testa o contexto RAG para uma query.
    Mostra exatamente o que seria enviado ao LLM.
    Útil para debug e validação.
    """
    try:
        context = get_context_for_query(body.query)
        search_results = search_knowledge(body.query, n_results=5)
        
        return SuccessResponse(data={
            "query": body.query,
            "context_for_llm": context,
            "context_length": len(context),
            "raw_results": search_results
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 📋 TEMPLATE MANAGEMENT ENDPOINTS (NEW)
# ============================================================

@router.post("/templates/upload", response_model=SuccessResponse)
async def upload_template_excel(
    file: UploadFile = File(...),
    cycle: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Upload e ingestão automática de arquivo Excel com templates
    
    **ADMIN ONLY**
    
    Args:
        file: Arquivo Excel (.xlsx)
        cycle: Identificador do cycle (ex: Q1, Q2, Q3)
        description: Descrição opcional do batch de templates
    
    Returns:
        Estatísticas da ingestão e lista de templates processados
    """
    try:
        # Validar extensão
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(
                status_code=400,
                detail="Only .xlsx files are supported"
            )
        
        # Ler conteúdo do arquivo
        file_content = await file.read()
        
        # Executar ingestão
        result = await upload_and_ingest_template(
            file_content=file_content,
            filename=file.filename,
            cycle=cycle,
            description=description,
            db=db
        )
        
        return SuccessResponse(data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=SuccessResponse)
async def list_templates(
    cycle: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Lista todos os templates registrados
    
    **ADMIN ONLY**
    
    Args:
        cycle: Filtrar por cycle (opcional)
    
    Returns:
        Lista de templates
    """
    try:
        templates = list_templates_by_cycle(cycle, db)
        return SuccessResponse(data={
            "templates": templates,
            "total": len(templates)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/cycles", response_model=SuccessResponse)
async def get_available_cycles(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Lista todos os cycles disponíveis
    
    **ADMIN ONLY**
    
    Returns:
        Lista de cycles
    """
    try:
        cycles = list_available_cycles(db)
        return SuccessResponse(data={
            "cycles": cycles,
            "total": len(cycles)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{cycle}/{template_key}", response_model=SuccessResponse)
async def get_template_details(
    cycle: str,
    template_key: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Busca detalhes de um template específico
    
    **ADMIN ONLY**
    
    Args:
        cycle: Cycle do template
        template_key: Chave do template
    
    Returns:
        Detalhes completos do template
    """
    try:
        template = get_template_by_key(cycle, template_key, db)
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_key}' not found in cycle '{cycle}'"
            )
        
        return SuccessResponse(data=template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdateTemplateStatusBody(BaseModel):
    status: str  # active, inactive, archived


@router.patch("/templates/{template_id}/status", response_model=SuccessResponse)
async def update_template_status_endpoint(
    template_id: int,
    body: UpdateTemplateStatusBody,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Atualiza status de um template
    
    **ADMIN ONLY**
    
    Args:
        template_id: ID do template
        body: Novo status
    
    Returns:
        Template atualizado
    """
    try:
        # Validar status
        valid_statuses = ["active", "inactive", "archived"]
        if body.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )
        
        template = update_template_status(template_id, body.status, db)
        return SuccessResponse(data=template)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====================================================================
# ENDPOINTS DE ONBOARDING (Invitations e Memberships)
# ====================================================================

from pydantic import Field
from services.onboarding import (
    create_invitation,
    revoke_invitation,
    revoke_membership,
    list_invitations,
    list_memberships,
    VALID_ROLES,
)
from db.models import Organization, Cycle, Membership, Invitation


class CreateInvitationRequest(BaseModel):
    """Request body para criar convite"""
    email: str = Field(..., description="Email do usuário a convidar")
    organization_id: int = Field(..., description="ID da organização")
    cycle_id: int = Field(..., description="ID do ciclo")
    role: str = Field(..., description=f"Role: {list(VALID_ROLES.keys())}")
    invitation_message: Optional[str] = Field(None, description="Mensagem personalizada")


class InvitationResponse(BaseModel):
    """Response com dados do convite (SEM token em plaintext)"""
    id: int
    email: str
    organization_id: int
    cycle_id: int
    role: str
    status: str
    expires_at: datetime
    created_at: datetime
    
    model_config = {"from_attributes": True}


class InvitationWithLinkResponse(BaseModel):
    """Response ao criar convite (contém link APENAS, nunca token em plaintext em logs)"""
    invitation_id: int
    email: str
    role: str
    expires_at: datetime
    invite_link: str  # URL para frontend aceitar convite
    expires_in_hours: int


@router.post("/invitations", response_model=InvitationWithLinkResponse)
async def create_invitation_endpoint(
    request: CreateInvitationRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Cria um convite para um usuário ingressar em uma org/ciclo.
    
    **ADMIN ONLY**
    
    Segurança:
    - Token é gerado securely (secrets.token_urlsafe)
    - Salva apenas hash SHA256
    - Nunca retorna token em logs
    - Retorna apenas invite_link para frontend
    - Invite link deve ser enviado via email fora deste endpoint
    
    Idempotência:
    - Se já existe convite PENDING para mesmo email/org/cycle:
      Retorna ID do convite existente (não cria novo token)
    
    Returns:
        Dados do convite + invite_link (sem token plaintext)
    """
    try:
        invitation, plain_token = create_invitation(
            db=db,
            email=request.email,
            organization_id=request.organization_id,
            cycle_id=request.cycle_id,
            role=request.role,
            invited_by_user_id=current_admin.id,
            invitation_message=request.invitation_message,
        )
        
        # Calcular TTL em horas
        from services.onboarding import INVITE_TOKEN_TTL_HOURS
        expires_in = int((invitation.expires_at - datetime.utcnow()).total_seconds() / 3600)
        
        # Construir invite_link (o token é passado para o frontend via query param)
        # Frontend vai enviar: POST /auth/accept-invitation com { token, password, name }
        frontend_base_url = __import__('os').getenv('FRONTEND_BASE_URL', 'http://localhost:3000')
        invite_link = f"{frontend_base_url}/auth/accept-invitation?token={plain_token}"
        
        logger_msg = (
            f"Convite criado para {request.email} "
            f"(id={invitation.id}, org={request.organization_id}, cycle={request.cycle_id})"
        )
        logger.info(logger_msg)  # Token NOT included in logs
        
        return InvitationWithLinkResponse(
            invitation_id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            expires_at=invitation.expires_at,
            invite_link=invite_link,
            expires_in_hours=expires_in,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao criar convite: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invitations", response_model=SuccessResponse)
async def list_invitations_endpoint(
    organization_id: Optional[int] = None,
    cycle_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Lista convites com filtros opcionais.
    
    **ADMIN ONLY**
    
    Filtros:
    - organization_id: Filtrar por organização
    - cycle_id: Filtrar por ciclo
    - status: pending|accepted|expired|revoked
    
    Returns:
        Lista paginada de convites (SEM tokens)
    """
    try:
        invitations, total = list_invitations(
            db=db,
            organization_id=organization_id,
            cycle_id=cycle_id,
            status=status,
            skip=skip,
            limit=limit,
        )
        
        invitations_data = [
            {
                'id': inv.id,
                'email': inv.email,
                'organization_id': inv.organization_id,
                'cycle_id': inv.cycle_id,
                'role': inv.role,
                'status': inv.status,
                'expires_at': inv.expires_at,
                'used_at': inv.used_at,
                'created_at': inv.created_at,
            }
            for inv in invitations
        ]
        
        return SuccessResponse(data={
            'invitations': invitations_data,
            'total': total,
            'skip': skip,
            'limit': limit,
        })
    
    except Exception as e:
        logger.error(f"Erro ao listar convites: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class RevokeInvitationRequest(BaseModel):
    """Request para revogar convite"""
    pass  # Body vazio, tudo via path param


@router.patch("/invitations/{invitation_id}/revoke", response_model=InvitationResponse)
async def revoke_invitation_endpoint(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Revoga um convite pendente.
    
    **ADMIN ONLY**
    
    Um convite revogado não pode mais ser aceito.
    """
    try:
        invitation = revoke_invitation(db, invitation_id)
        
        logger.info(f"Convite {invitation_id} revogado por {current_admin.email}")
        
        return InvitationResponse.model_validate(invitation)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao revogar convite: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ====================================================================
# Endpoints de Membership (Autorização / Contexto)
# ====================================================================

class MembershipResponse(BaseModel):
    """Response com dados de membership"""
    id: int
    user_id: str
    organization_id: int
    cycle_id: int
    role: str
    status: str
    created_at: datetime
    revoked_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


@router.get("/memberships", response_model=SuccessResponse)
async def list_memberships_endpoint(
    organization_id: Optional[int] = None,
    cycle_id: Optional[int] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Lista memberships com filtros opcionais.
    
    **ADMIN ONLY**
    
    Filtros:
    - organization_id: Por organização
    - cycle_id: Por ciclo
    - status: active|revoked|invited
    - role: admin_fcj|mentor|founder
    
    Returns:
        Lista paginada de memberships
    """
    try:
        memberships, total = list_memberships(
            db=db,
            organization_id=organization_id,
            cycle_id=cycle_id,
            status=status,
            role=role,
            skip=skip,
            limit=limit,
        )
        
        memberships_data = [
            {
                'id': m.id,
                'user_id': m.user_id,
                'organization_id': m.organization_id,
                'cycle_id': m.cycle_id,
                'role': m.role,
                'status': m.status,
                'created_at': m.created_at,
                'revoked_at': m.revoked_at,
            }
            for m in memberships
        ]
        
        return SuccessResponse(data={
            'memberships': memberships_data,
            'total': total,
            'skip': skip,
            'limit': limit,
        })
    
    except Exception as e:
        logger.error(f"Erro ao listar memberships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/memberships/{membership_id}/revoke", response_model=MembershipResponse)
async def revoke_membership_endpoint(
    membership_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Revoga acesso de um usuário a uma org/ciclo.
    
    **ADMIN ONLY**
    
    Um membership revogado bloqueia imediatamente o acesso.
    """
    try:
        membership = revoke_membership(db, membership_id)
        
        logger.info(
            f"Membership {membership_id} revogado para user {membership.user_id} "
            f"por {current_admin.email}"
        )
        
        return MembershipResponse.model_validate(membership)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao revogar membership: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))