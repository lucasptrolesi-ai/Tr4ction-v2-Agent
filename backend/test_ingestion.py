"""
Script de teste do pipeline de ingestão de templates

Simula upload de Template Q1.xlsx via API admin
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from db.database import SessionLocal
from services.template_ingestion_service import TemplateIngestionService


def test_ingestion():
    """Testa ingestão do Template Q1.xlsx"""
    
    # Path do arquivo Excel (na raiz do projeto)
    excel_path = backend_dir.parent / "Template Q1.xlsx"
    
    if not excel_path.exists():
        print(f"❌ Arquivo não encontrado: {excel_path}")
        return False
    
    print(f"📁 Arquivo encontrado: {excel_path}")
    print(f"📊 Tamanho: {excel_path.stat().st_size / 1024:.2f} KB\n")
    
    # Criar sessão do banco
    db = SessionLocal()
    
    try:
        # Instanciar serviço
        service = TemplateIngestionService(db)
        
        print("🚀 Iniciando ingestão do cycle 'Q1'...\n")
        
        # Executar ingestão
        result = service.ingest_excel_file(
            file_path=str(excel_path),
            cycle="Q1",
            description="Templates Q1 - Gerado automaticamente pelo sistema"
        )
        
        # Exibir resultados
        print("\n" + "=" * 60)
        print("📊 RESULTADO DA INGESTÃO")
        print("=" * 60)
        print(f"Cycle: {result['cycle']}")
        print(f"Total de sheets: {result['total_sheets']}")
        print(f"Sucesso: {result['successful']}")
        print(f"Falhas: {result['failed']}")
        print(f"Total de campos: {result['total_fields']}")
        print(f"Registrados no banco: {result['registered_in_db']}")
        print(f"Relatório: {result['report_path']}")
        print("=" * 60)
        
        # Exibir templates processados
        print("\n📋 Templates processados:\n")
        for r in result['results']:
            status = "✅" if r['success'] else "❌"
            warnings = f" ({len(r['warnings'])} warnings)" if r['warnings'] else ""
            print(f"{status} {r['template_key']:30} | {r['field_count']:3} campos{warnings}")
        
        print(f"\n✅ Ingestão concluída com sucesso!")
        print(f"\n📄 Leia o relatório completo em: {result['report_path']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante ingestão: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = test_ingestion()
    sys.exit(0 if success else 1)
