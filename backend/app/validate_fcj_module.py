"""
Script de teste rápido do módulo FCJ Ingestion
==============================================

Valida pipeline completo sem necessidade de servidor rodando.

Uso:
    python backend/app/validate_fcj_module.py path/to/template.xlsx Q1
"""

import sys
import argparse
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.template_snapshot import TemplateSnapshotService, validate_snapshot
from app.services.fillable_detector import FillableAreaDetector


def main():
    parser = argparse.ArgumentParser(description="Valida módulo FCJ Ingestion")
    parser.add_argument("xlsx_file", help="Caminho para arquivo .xlsx")
    parser.add_argument("cycle", help="Cycle FCJ (ex: Q1, Q2)")
    args = parser.parse_args()
    
    xlsx_path = Path(args.xlsx_file)
    if not xlsx_path.exists():
        print(f"❌ Arquivo não encontrado: {xlsx_path}")
        sys.exit(1)
    
    print(f"📊 Validando template: {xlsx_path.name}")
    print(f"🎯 Cycle: {args.cycle}")
    print("-" * 60)
    
    # 1. Ler arquivo
    with open(xlsx_path, "rb") as f:
        file_bytes = f.read()
    
    print(f"✓ Arquivo lido: {len(file_bytes)} bytes")
    
    # 2. Extrair snapshot
    print("\n📸 Extraindo snapshot...")
    snapshot_service = TemplateSnapshotService()
    try:
        snapshot, assets = snapshot_service.extract(file_bytes)
        print(f"✓ Snapshot extraído:")
        print(f"  - Schema version: {snapshot['schema_version']}")
        print(f"  - Sheets: {len(snapshot['sheets'])}")
        print(f"  - Assets: {len(assets)}")
    except Exception as e:
        print(f"❌ Erro na extração: {e}")
        sys.exit(1)
    
    # 3. Validar snapshot
    print("\n🔍 Validando snapshot...")
    validation = validate_snapshot(snapshot)
    if validation["valid"]:
        print("✓ Snapshot válido!")
        stats = validation["stats"]
        print(f"  - Total células: {stats['total_cells']}")
        print(f"  - Merged ranges: {stats['total_merged']}")
        print(f"  - Validations: {stats['total_validations']}")
        print(f"  - Images: {stats['total_images']}")
    else:
        print("❌ Snapshot INVÁLIDO:")
        for error in validation["errors"]:
            print(f"  - {error}")
        sys.exit(1)
    
    # 4. Detectar fillable areas
    print("\n🔍 Detectando áreas preenchíveis...")
    detector = FillableAreaDetector()
    try:
        candidates = detector.detect(snapshot)
        print(f"✓ Detectados {len(candidates)} campos preenchíveis:")
        
        # Agrupar por sheet
        by_sheet = {}
        for c in candidates:
            if c.sheet not in by_sheet:
                by_sheet[c.sheet] = []
            by_sheet[c.sheet].append(c)
        
        for sheet, fields in by_sheet.items():
            print(f"\n  📄 {sheet}:")
            for f in fields[:5]:  # Mostrar primeiros 5
                label = f.label or "(sem label)"
                print(f"    - {f.cell_range}: {label} [{f.inferred_type}]")
            if len(fields) > 5:
                print(f"    ... e mais {len(fields) - 5} campos")
    except Exception as e:
        print(f"❌ Erro na detecção: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 5. Resumo final
    print("\n" + "=" * 60)
    print("✅ VALIDAÇÃO COMPLETA")
    print("=" * 60)
    print(f"Template: {xlsx_path.name}")
    print(f"Cycle: {args.cycle}")
    print(f"Sheets: {len(snapshot['sheets'])}")
    print(f"Campos detectados: {len(candidates)}")
    print(f"Schema version: {snapshot['schema_version']}")
    print("\n💾 Pronto para upload via endpoint /admin/templates/upload")


if __name__ == "__main__":
    main()
