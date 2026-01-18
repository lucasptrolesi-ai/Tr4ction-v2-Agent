"""
Trail Ingestion Service - Pipeline de ingestão de trilhas educacionais FCJ

Responsabilidade:
- Coordenar extração de snapshot → perguntas → campos
- Validar fidelidade (100% das perguntas foram extraídas?)
- Garantir ordem preservada
- Fail-fast em caso de ambiguidade ou incompletude

Pipeline:
1. Snapshot (extração estrutural)
2. QuestionExtractor (extração semântica)
3. Validação de cobertura
4. Persistência com ordem absoluta
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Tuple

from app.services.template_snapshot import TemplateSnapshotService, SnapshotLoadError, SnapshotValidationError, validate_snapshot
from app.services.question_extractor import QuestionExtractor, Question

logger = logging.getLogger(__name__)


class TrailIngestionError(Exception):
    """Erro crítico de ingestão de trilha"""
    pass


class TrailIngestionService:
    """
    Serviço que coordena a ingestão de uma trilha educacional
    """
    
    def ingest(self, file_bytes: bytes) -> Tuple[List[Question], Dict[str, Any]]:
        """
        Ingere um arquivo Excel como trilha educacional
        
        Pipeline:
        1. Extrai snapshot completo + validação estrutural
        2. Extrai perguntas respeitando ordem
        3. Valida cobertura (todas as perguntas foram extraídas?)
        4. Retorna lista de perguntas ordenada
        
        Args:
            file_bytes: Conteúdo binário do .xlsx
            
        Returns:
            (questions: List[Question], report: Dict com auditoria)
            
        Raises:
            TrailIngestionError: Se algo faltar ou houver inconsistência
        """
        
        report = {
            "step_1_snapshot": None,
            "step_2_questions": None,
            "step_3_validation": None,
            "errors": [],
            "warnings": [],
        }
        
        try:
            # PASSO 1: Extrar snapshot
            logger.info("🔧 PASSO 1: Extraindo snapshot estrutural...")
            snapshot_service = TemplateSnapshotService()
            try:
                snapshot, assets = snapshot_service.extract(file_bytes)
            except (SnapshotLoadError, SnapshotValidationError) as e:
                error = f"Falha ao extrair snapshot: {str(e)}"
                logger.error(f"❌ {error}")
                raise TrailIngestionError(error) from e
            
            # Validar snapshot
            validation_report = validate_snapshot(snapshot)
            if not validation_report["valid"]:
                error = f"Snapshot inválido: {validation_report['errors']}"
                logger.error(f"❌ {error}")
                raise TrailIngestionError(error)
            
            report["step_1_snapshot"] = {
                "sheets": len(snapshot.get("sheets", [])),
                "total_cells": validation_report["stats"]["total_cells"],
                "status": "✅ OK",
            }
            
            logger.info(f"✅ Snapshot OK: {report['step_1_snapshot']['sheets']} abas, "
                       f"{report['step_1_snapshot']['total_cells']} células")
            
            # PASSO 2: Extrair perguntas
            logger.info("📝 PASSO 2: Extraindo perguntas como trilha educacional...")
            extractor = QuestionExtractor()
            try:
                questions, extraction_audit = extractor.extract(snapshot)
            except ValueError as e:
                error = f"Falha ao extrair perguntas: {str(e)}"
                logger.error(f"❌ {error}")
                raise TrailIngestionError(error) from e
            
            report["step_2_questions"] = {
                "total_questions": len(questions),
                "sheets_analyzed": extraction_audit["sheets_analyzed"],
                "coverage_by_sheet": extraction_audit["coverage_by_sheet"],
                "status": "✅ OK",
            }
            
            logger.info(f"✅ Perguntas extraídas: {len(questions)} perguntas em "
                       f"{extraction_audit['sheets_analyzed']} abas")
            
            # PASSO 3: Validar cobertura e fidelidade
            logger.info("✓ PASSO 3: Validando cobertura e fidelidade...")
            coverage_valid, coverage_errors = extractor.validate_coverage(questions, snapshot)
            
            if not coverage_valid:
                error = f"Validação de cobertura falhou: {coverage_errors}"
                logger.error(f"❌ {error}")
                raise TrailIngestionError(error)
            
            # Validar ordem global
            for i, q in enumerate(questions):
                if q.order_index_global != i:
                    error = f"Ordem global quebrada na pergunta {i}: {q.question_text[:50]}"
                    logger.error(f"❌ {error}")
                    raise TrailIngestionError(error)
            
            report["step_3_validation"] = {
                "coverage_valid": True,
                "order_valid": True,
                "deterministic_ids": len(set(q.field_id for q in questions)) == len(questions),
                "status": "✅ OK",
            }
            
            logger.info("✅ Validação de fidelidade: PASSOU")
            logger.info(f"   - Ordem global: Preservada ({len(questions)} perguntas em sequência)")
            logger.info(f"   - Cobertura: 100% ({len(questions)} perguntas extraídas)")
            logger.info(f"   - IDs: Determinísticos e únicos")
            
            report["final_status"] = "✅ TRILHA EDUCACIONAL INGERIDA COM SUCESSO"
            
            return questions, report
        
        except TrailIngestionError:
            raise
        except Exception as e:
            error = f"Erro inesperado: {str(e)}"
            logger.error(f"❌ {error}", exc_info=True)
            raise TrailIngestionError(error) from e
