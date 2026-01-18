"""
Testes para validação de dependências XLSX no boot

Verifica:
1. Dependências estão instaladas
2. Serviços podem ser instanciados
3. Erro claro se algo faltar
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.xlsx_validator import (
    XlsxDependencyValidator,
    validate_xlsx_support_on_startup,
    DependencyCheckError
)


def test_xlsx_validator_checks_imports():
    """Verifica que validador checa imports"""
    success, errors = XlsxDependencyValidator._check_basic_imports()
    
    assert success, f"Imports falharam: {errors}"


def test_xlsx_validator_checks_services():
    """Verifica que validador checa serviços"""
    success, errors = XlsxDependencyValidator._check_services()
    
    assert success, f"Serviços falharam: {errors}"


def test_xlsx_validator_validate_all():
    """Verifica validação completa"""
    success, errors = XlsxDependencyValidator.validate_all()
    
    assert success, f"Validação XLSX falhou: {errors}"


def test_xlsx_support_on_startup():
    """Verifica que startup validation funciona"""
    # Não deve lançar exceção
    try:
        validate_xlsx_support_on_startup()
    except DependencyCheckError as e:
        pytest.fail(f"Validação XLSX falhou no startup: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
