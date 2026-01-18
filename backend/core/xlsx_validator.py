"""
Health Check e Validação de Dependências - Fail Fast em Produção

Verifica na inicialização que:
- Todas as dependências Excel estão instaladas
- Snapshot service pode ser instanciado
- Detector pode ser instanciado
- Registry pode ser instanciado
"""

import logging
import sys
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class DependencyCheckError(Exception):
    """Erro crítico de dependência"""
    pass


class XlsxDependencyValidator:
    """Valida dependências XLSX necessárias"""
    
    REQUIRED_PACKAGES = {
        "openpyxl": "3.1.2",
        "Pillow": "10.1.0",
        "lxml": "4.9.3",
        "python-dateutil": "2.8.2",
    }
    
    @classmethod
    def validate_all(cls) -> Tuple[bool, List[str]]:
        """
        Valida todas as dependências XLSX
        
        Returns:
            (success: bool, errors: List[str])
        """
        errors = []
        
        # 1. Validar imports básicos
        basic_deps = cls._check_basic_imports()
        if not basic_deps[0]:
            errors.extend(basic_deps[1])
        
        # 2. Validar serviços podem ser instanciados
        service_check = cls._check_services()
        if not service_check[0]:
            errors.extend(service_check[1])
        
        return len(errors) == 0, errors
    
    @classmethod
    def _check_basic_imports(cls) -> Tuple[bool, List[str]]:
        """Verifica que imports básicos funcionam"""
        errors = []
        
        try:
            import openpyxl
            logger.info(f"✓ openpyxl {openpyxl.__version__}")
        except ImportError as e:
            errors.append(f"❌ openpyxl não instalado: {e}")
        
        try:
            import PIL
            logger.info(f"✓ Pillow (PIL) instalado")
        except ImportError as e:
            errors.append(f"❌ Pillow não instalado: {e}")
        
        try:
            import lxml
            logger.info(f"✓ lxml instalado")
        except ImportError as e:
            errors.append(f"❌ lxml não instalado: {e}")
        
        try:
            import dateutil
            logger.info(f"✓ python-dateutil instalado")
        except ImportError as e:
            errors.append(f"❌ python-dateutil não instalado: {e}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def _check_services(cls) -> Tuple[bool, List[str]]:
        """Verifica que serviços podem ser instanciados"""
        errors = []
        
        try:
            from app.services.template_snapshot import TemplateSnapshotService
            service = TemplateSnapshotService()
            logger.info("✓ TemplateSnapshotService instanciado com sucesso")
        except Exception as e:
            errors.append(f"❌ Falha ao instanciar TemplateSnapshotService: {e}")
        
        try:
            from app.services.fillable_detector import FillableAreaDetector
            detector = FillableAreaDetector()
            logger.info("✓ FillableAreaDetector instanciado com sucesso")
        except Exception as e:
            errors.append(f"❌ Falha ao instanciar FillableAreaDetector: {e}")
        
        try:
            from app.services.template_registry import TemplateRegistry
            registry = TemplateRegistry()
            logger.info("✓ TemplateRegistry instanciado com sucesso")
        except Exception as e:
            errors.append(f"❌ Falha ao instanciar TemplateRegistry: {e}")
        
        return len(errors) == 0, errors


def validate_xlsx_support_on_startup() -> None:
    """
    Valida suporte XLSX na inicialização
    
    Se houver erro, falha imediatamente (fail fast)
    
    Raises:
        DependencyCheckError: Se validação falhar
    """
    logger.info("=" * 60)
    logger.info("🔍 Validando suporte XLSX (.xlsx)...")
    logger.info("=" * 60)
    
    success, errors = XlsxDependencyValidator.validate_all()
    
    if not success:
        error_msg = "\n".join(errors)
        logger.error(f"\n❌ ERRO CRÍTICO - Suporte XLSX não funcional:\n{error_msg}")
        logger.error("=" * 60)
        raise DependencyCheckError(
            f"Suporte XLSX inválido. Por favor instale dependências:\n{error_msg}"
        )
    
    logger.info("✅ Suporte XLSX validado com sucesso!")
    logger.info("=" * 60)
