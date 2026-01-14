from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os

from core.models import SuccessResponse
from db.database import get_db
from db.models import Trail, StepSchema, StepAnswer, UserProgress
from services.xlsx_exporter import generate_xlsx
from services.auth import get_current_user_id, get_current_user, get_current_founder
from db.models import User

# Imports enterprise (podem não existir em todos os deploys)
try:
    from enterprise.config import get_or_create_enterprise_config
    from enterprise.client_premises import ClientPremiseService
    from enterprise.governance.engine import GovernanceEngine
    from enterprise.governance.models import GovernanceGateService
    from enterprise.risk_engine.detector import RiskDetectionEngine
    ENTERPRISE_AVAILABLE = True
except ImportError:
    ENTERPRISE_AVAILABLE = False
    # Fallback mocks
    def get_or_create_enterprise_config():
        class MockConfig:
            method_governance = False
            enable_governance_gates = False
            risk_engine = False
            enable_risk_blocking = False
            ai_audit = False
        return MockConfig()
from backend.enterprise.risk_engine.models import RiskSignalService
from backend.enterprise.cognitive_signals import CognitiveUXFormatter

router = APIRouter(prefix="/founder")
logger = logging.getLogger(__name__)


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


def compute_cognitive_signals(
    *,
    template_key: str,
    data: Dict[str, Any],
    db: Session,
    previous_data: Optional[Dict[str, Any]] = None,
    startup_id: Optional[str] = None,
    partner_id: Optional[str] = None,
    vertical_id: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Compute cognitive_signals payload from risk/governance without blocking.
    
    Phase 4: Now supports partner/vertical context for language tone.
    """
    config = get_or_create_enterprise_config()
    
    # Build execution context (Phase 4)
    language_tone = "consultative"  # Default
    if config.multi_vertical:
        try:
            from backend.enterprise.multi_vertical.context import ContextBuilder
            builder = ContextBuilder(db)
            context = builder.build(
                startup_id=startup_id or template_key,
                user_id=startup_id or template_key,
                template_key=template_key,
                partner_id=partner_id,
                vertical_id=vertical_id,
            )
            language_tone = context.language_tone
        except Exception as ctx_exc:
            logger.debug("Context builder unavailable, using defaults: %s", ctx_exc)
    
    premise_service = ClientPremiseService(db)
    premises_result = premise_service.ensure_premise_or_fallback(startup_id or template_key)
    premises_payload = premises_result.get("premises") if premises_result else None

    governance_results = []
    risk_result_dict: Optional[Dict[str, Any]] = None

    try:
        if config.method_governance or config.enable_governance_gates:
            gate_service = GovernanceGateService(db)
            gate = gate_service.latest_gate(template_key, vertical=None)
            if gate:
                gate_result = GovernanceEngine().evaluate_gate(
                    gate,
                    template_key=template_key,
                    data=data,
                    previous_data=previous_data,
                )
                governance_results.append(gate_result.to_dict())
    except Exception as exc:
        logger.warning("Governance signal skipped for %s: %s", template_key, exc)

    try:
        if config.risk_engine or config.enable_risk_blocking:
            risk_engine = RiskDetectionEngine()
            assessment = risk_engine.assess_template_response(
                template_key=template_key,
                data=data,
                previous_versions=[previous_data] if previous_data else None,
                related_templates=None,
                premises=premises_payload,
            )
            risk_result_dict = assessment.to_dict()

            # Persist observational signal
            try:
                RiskSignalService(db).record_signal(
                    client_id=startup_id or template_key,
                    template_key=template_key,
                    risk_type="overall",
                    severity=risk_result_dict.get("overall_risk", "low"),
                    evidence=[f for f in risk_result_dict.get("red_flags", [])],
                    violated_dependencies=[
                        dep
                        for flag in risk_result_dict.get("red_flags", [])
                        for dep in (flag.get("violated_dependencies") or [])
                        if isinstance(flag, dict)
                    ],
                    recommendation="Revise itens com risco alto/crítico antes de avançar.",
                    related_decisions=None,
                )
            except Exception as signal_exc:
                logger.debug("Risk signal persistence skipped: %s", signal_exc)
    except Exception as exc:
        logger.warning("Risk signal skipped for %s: %s", template_key, exc)

    formatter = CognitiveUXFormatter()
    cognitive_signals = formatter.build(
        risk_result=risk_result_dict,
        governance_results=governance_results,
        blocking_enabled=config.enable_risk_blocking,
        language_tone=language_tone,  # Phase 4: Apply partner-specific tone
    )
    
    # Phase 4: Add partner/vertical context to response
    if partner_id or vertical_id:
        cognitive_signals = cognitive_signals or {}
        cognitive_signals["partner_id"] = partner_id
        cognitive_signals["vertical_id"] = vertical_id

    return cognitive_signals, risk_result_dict


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

        cognitive_signals = None
        try:
            cognitive_signals, _ = compute_cognitive_signals(
                template_key=step_id,
                data=answer.answers if answer else {},
                previous_data=None,
                db=db,
                startup_id=user_id,
            )
        except Exception as signal_exc:
            logger.debug("Cognitive signals unavailable for %s/%s: %s", trail_id, step_id, signal_exc)
        
        return {
            "trail_id": trail_id,
            "step_id": step_id,
            "isLocked": progress.is_locked if progress else False,
            "formData": answer.answers if answer else {},
            "cognitive_signals": cognitive_signals,
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
        previous_answers = answer.answers if answer else None
        
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

        cognitive_signals = None
        risk_result = None
        try:
            cognitive_signals, risk_result = compute_cognitive_signals(
                template_key=step_id,
                data=body.formData,
                previous_data=previous_answers,
                db=db,
                startup_id=user_id,
            )
        except Exception as signal_exc:
            logger.debug("Cognitive signals generation skipped for %s/%s: %s", trail_id, step_id, signal_exc)
        
        return SuccessResponse(data={
            "trail_id": trail_id,
            "step_id": step_id,
            "saved": True,
            "cognitive_signals": cognitive_signals,
            "risk_result": risk_result,
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
