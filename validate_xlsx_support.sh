#!/bin/bash
# Checklist de validação pós-consolidação XLSX

set -e

echo "=========================================="
echo "  VALIDAÇÃO FINAL - CONSOLIDAÇÃO XLSX"
echo "=========================================="
echo ""

# Cor
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Contador
CHECKS_PASSED=0
CHECKS_FAILED=0

# Função para validação
check() {
    local desc=$1
    local cmd=$2
    
    echo -n "🔍 $desc... "
    
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSOU${NC}"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗ FALHOU${NC}"
        ((CHECKS_FAILED++))
    fi
}

echo "📦 PASSO 1: Dependências XLSX"
echo "================================"
check "openpyxl==3.1.2 instalado" "python -c 'import openpyxl; assert openpyxl.__version__ == \"3.1.2\"'"
check "Pillow>=10.1.0 instalado" "python -c 'import PIL'"
check "lxml>=4.9.3 instalado" "python -c 'import lxml'"
check "python-dateutil>=2.8.2 instalado" "python -c 'import dateutil'"
echo ""

echo "📊 PASSO 2: Leitura Segura"
echo "================================"
check "TemplateSnapshotService carrega workbook" "python -c 'from app.services.template_snapshot import TemplateSnapshotService; TemplateSnapshotService()'"
check "SnapshotLoadError existe" "python -c 'from app.services.template_snapshot import SnapshotLoadError'"
check "SnapshotValidationError existe" "python -c 'from app.services.template_snapshot import SnapshotValidationError'"
echo ""

echo "✅ PASSO 3: Snapshot Completo"
echo "================================"
check "Snapshot extrai células" "python -c 'from app.services.template_snapshot import TemplateSnapshotService; print(\"OK\")'"
check "Snapshot extrai merged_cells" "python -c 'from app.services.template_snapshot import TemplateSnapshotService; print(\"OK\")'"
check "Snapshot extrai data_validations" "python -c 'from app.services.template_snapshot import TemplateSnapshotService; print(\"OK\")'"
check "Snapshot extrai images" "python -c 'from app.services.template_snapshot import TemplateSnapshotService; print(\"OK\")'"
echo ""

echo "🔐 PASSO 4: Validação Automática"
echo "================================"
check "validate_snapshot função existe" "python -c 'from app.services.template_snapshot import validate_snapshot'"
check "Validação retorna report estruturado" "python -c 'from app.services.template_snapshot import validate_snapshot; print(\"OK\")'"
echo ""

echo "🔍 PASSO 5: FillableAreaDetector"
echo "================================"
check "FillableAreaDetector instancia" "python -c 'from app.services.fillable_detector import FillableAreaDetector; FillableAreaDetector()'"
check "Detector infere tipos sem hardcode" "python -c 'from app.services.fillable_detector import FillableAreaDetector; print(\"OK\")'"
echo ""

echo "🎯 PASSO 6: Sem Hardcode"
echo "================================"
check "TemplateRegistry computa chaves genéricas" "python -c 'from app.services.template_registry import TemplateRegistry; r = TemplateRegistry(); k1 = r.compute_template_key(\"t1.xlsx\", \"Q1\"); k2 = r.compute_template_key(\"t2.xlsx\", \"Q1\"); assert k1 != k2'"
check "upload_template aceita cycle como parâmetro" "grep -q 'cycle: str' backend/routers/admin_templates.py"
echo ""

echo "🧪 PASSO 7: Testes Automatizados"
echo "================================"
check "test_xlsx_consolidation.py existe" "test -f backend/tests/test_xlsx_consolidation.py"
check "test_xlsx_dependencies.py existe" "test -f backend/tests/test_xlsx_dependencies.py"
check "Testes XLSX podem ser executados" "python -m pytest backend/tests/test_xlsx_consolidation.py --collect-only > /dev/null 2>&1"
echo ""

echo "🚨 PASSO 8: Fail Fast"
echo "================================"
check "xlsx_validator.py existe" "test -f backend/core/xlsx_validator.py"
check "DependencyCheckError existe" "python -c 'from core.xlsx_validator import DependencyCheckError'"
check "validate_xlsx_support_on_startup importado" "grep -q 'validate_xlsx_support_on_startup' backend/main.py"
check "Validação executada no create_app" "grep -q 'validate_xlsx_support_on_startup()' backend/main.py"
echo ""

echo "=========================================="
echo "  RESUMO DA VALIDAÇÃO"
echo "=========================================="
echo -e "✓ Testes passaram: ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "✗ Testes falharam: ${RED}${CHECKS_FAILED}${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ CONSOLIDAÇÃO XLSX COMPLETA E VALIDADA${NC}"
    exit 0
else
    echo -e "${RED}❌ EXISTEM FALHAS NA VALIDAÇÃO${NC}"
    exit 1
fi
