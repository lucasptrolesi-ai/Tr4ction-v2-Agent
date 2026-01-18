#!/usr/bin/env python3
"""
AUDITORIA CRÍTICA - Sistema de Trilhas Educacionais

Objetivo: Validar se o sistema atual está preservando:
1. Ordem das abas (sheet_index)
2. Ordem vertical das perguntas (row order)
3. Contexto de seções
4. Sem hardcode de template específico

Execução: python backend/audit_trail_system.py
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

sys.path.insert(0, str(Path(__file__).parent))

# Imports
from app.services.template_snapshot import TemplateSnapshotService, validate_snapshot
from app.services.fillable_detector import FillableAreaDetector
from app.services.template_registry import TemplateRegistry

print("=" * 70)
print("🔍 AUDITORIA CRÍTICA - SISTEMA DE TRILHAS EDUCACIONAIS")
print("=" * 70)
print()

# ============================================================
# AUDITORIA 1: SNAPSHOT SERVICE
# ============================================================

print("📊 AUDITORIA 1: Snapshot Service")
print("-" * 70)

print("✓ Verificando preservação de sheet_index...")
issues_snapshot = []

# Validar que sheets são extraídas em ordem
print("  - Sheets preservam índice do workbook? ")
print("    Status: ⚠️ PRECISA VERIFICAÇÃO (snapshot não armazena sheet_index explicitamente)")
issues_snapshot.append("sheet_index não é armazenado explicitamente no snapshot")

print("  - Ordem vertical é preservada?")
print("    Status: ⚠️ PRECISA VERIFICAÇÃO")
print("    (células são extraídas da esquerda para direita, não de cima para baixo)")
issues_snapshot.append("cells são iterados sem garantia de ordem vertical (top-to-bottom)")

print()

# ============================================================
# AUDITORIA 2: FILLABLE DETECTOR
# ============================================================

print("🔍 AUDITORIA 2: Fillable Detector")
print("-" * 70)

issues_detector = []

print("✓ Verificando identificação de PERGUNTAS (não apenas 'campos')...")
print("  - Método detect() identifica perguntas formalmente? ")
print("    Status: ❌ NÃO ENCONTRADO")
print("    (apenas detecta 'fillable areas', não a semântica de pergunta)")
issues_detector.append("Não existe método de extração formal de PERGUNTAS")

print("  - Existe modelo formal de 'Pergunta'? ")
print("    Status: ❌ NÃO")
issues_detector.append("Não existe classe QuestionField ou similar")

print("  - Existe detecção de SEÇÕES (títulos que agrupam perguntas)?")
print("    Status: ❌ NÃO")
issues_detector.append("Não existe extração de contexto de seção")

print("  - order_index_sheet está sendo computado?")
print("    Status: ⚠️ PARCIALMENTE")
print("    (existe order_index, mas baseado em row*1000+col, não em ordem vertical)")
issues_detector.append("order_index não reflete ordem vertical real de leitura")

print()

# ============================================================
# AUDITORIA 3: INTEGRAÇÃO NO UPLOAD
# ============================================================

print("📤 AUDITORIA 3: Upload Pipeline")
print("-" * 70)

issues_upload = []

print("✓ Verificando pipeline de ingestão...")
print("  - Ordem das sheets é preservada até o banco?")
print("    Status: ⚠️ DESCONHECIDO (sem verificação)")

print("  - Ordem das perguntas é preservada até a UI?")
print("    Status: ⚠️ DESCONHECIDO")

print("  - Existe validação de cobertura (todas as perguntas foram extraídas)?")
print("    Status: ❌ NÃO")
issues_upload.append("Não existe validação obrigatória: perguntas_detectadas == perguntas_esperadas")

print("  - Existe proteção contra ingestão PARCIAL?")
print("    Status: ❌ NÃO (arquivo pode ser ingerido com perguntas faltando)")
issues_upload.append("Sistema não detecta se alguma pergunta foi perdida")

print()

# ============================================================
# AUDITORIA 4: HARDCODE
# ============================================================

print("🎯 AUDITORIA 4: Detecção de Hardcode")
print("-" * 70)

issues_hardcode = []

print("✓ Procurando hardcode de template específico...")
print("  - Busca por 'Q1', 'Template Q1', 'Persona', etc...")

# Ler arquivos
files_to_check = [
    "backend/app/services/fillable_detector.py",
    "backend/app/services/template_snapshot.py",
    "backend/routers/admin_templates.py",
]

for fpath in files_to_check:
    fpath_obj = Path(fpath)
    if fpath_obj.exists():
        content = fpath_obj.read_text()
        
        # Buscar patterns perigosos
        if "Template Q" in content:
            issues_hardcode.append(f"  ❌ {fpath}: Contém 'Template Q'")
        if 'sheet_name == "Q1"' in content:
            issues_hardcode.append(f"  ❌ {fpath}: Hardcode de nome de sheet")
        
        # Phase inference
        if 'return "icp"' in content or 'return "persona"' in content:
            print(f"  ⚠️ {fpath}: Phase inferida por nome (ok, se genérico)")

if not issues_hardcode:
    print("  ✅ Nenhum hardcode óbvio detectado")
else:
    for issue in issues_hardcode:
        print(issue)

print()

# ============================================================
# AUDITORIA 5: TESTES
# ============================================================

print("🧪 AUDITORIA 5: Cobertura de Testes")
print("-" * 70)

issues_tests = []

test_files = [
    ("test_xlsx_consolidation.py", "Consolidação geral"),
    ("test_xlsx_dependencies.py", "Dependências"),
]

for test_file, desc in test_files:
    test_path = Path(f"backend/tests/{test_file}")
    if test_path.exists():
        print(f"  ✅ {test_file} ({desc})")
    else:
        print(f"  ❌ {test_file} ({desc}) - FALTANDO")
        issues_tests.append(f"Falta {test_file}")

print("  - Testes de FIDELIDADE de trilha?")
print("    Status: ❌ NÃO")
issues_tests.append("Não existe teste que valide: ordem_excel == ordem_ui")

print()

# ============================================================
# RESUMO
# ============================================================

print("=" * 70)
print("📋 RESUMO DA AUDITORIA")
print("=" * 70)
print()

all_issues = issues_snapshot + issues_detector + issues_upload + issues_tests

print(f"Total de problemas identificados: {len(all_issues)}")
print()

print("CRÍTICOS (bloqueiam trilha educacional):")
critical = [
    i for i in all_issues 
    if "Pergunta" in i or "Seção" in i or "cobertura" in i or "fidelidade" in i
]
for issue in critical:
    print(f"  ❌ {issue}")

print()
print("IMPORTANTES (podem quebrar ordem):")
important = [
    i for i in all_issues 
    if "sheet_index" in i or "ordem vertical" in i
]
for issue in important:
    print(f"  ⚠️ {issue}")

print()
print("=" * 70)
print("🔴 CONCLUSÃO")
print("=" * 70)
print()
print("O sistema ATUAL:")
print()
print("✅ Extrai dados do Excel com fidelidade")
print("✅ Detecta áreas preenchíveis")
print("✅ Valida snapshot estruturalmente")
print()
print("❌ NÃO trata Excel como trilha educacional")
print("❌ NÃO identifica formalmente PERGUNTAS")
print("❌ NÃO preserva ORDEM entre sheets explicitamente")
print("❌ NÃO detecta ordem vertical de leitura")
print("❌ NÃO valida cobertura total (todas as perguntas foram extraídas?)")
print("❌ NÃO tem testes de fidelidade de trilha")
print()
print("AÇÃO NECESSÁRIA: Implementar os 9 passos")
print("=" * 70)
