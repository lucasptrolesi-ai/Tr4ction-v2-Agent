"""
Testa endpoints da API de templates
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from db.database import SessionLocal
from services.template_registry import get_registry


def test_registry_endpoints():
    """Testa descoberta de templates via registry"""
    
    db = SessionLocal()
    
    try:
        registry = get_registry(db)
        
        print("=" * 60)
        print("🔍 TESTE DO TEMPLATE REGISTRY")
        print("=" * 60)
        
        # 1. Listar cycles
        print("\n1️⃣ Listar cycles disponíveis:")
        cycles = registry.list_available_cycles()
        print(f"   Cycles: {cycles}")
        print(f"   Total: {len(cycles)}")
        
        # 2. Listar todos os templates
        print("\n2️⃣ Listar TODOS os templates:")
        all_templates = registry.list_all_templates()
        print(f"   Total de templates: {len(all_templates)}")
        for t in all_templates[:3]:
            print(f"   - {t['cycle']}/{t['template_key']} ({t['field_count']} campos)")
        if len(all_templates) > 3:
            print(f"   ... e mais {len(all_templates) - 3} templates")
        
        # 3. Listar templates do Q1
        print("\n3️⃣ Listar templates do cycle Q1:")
        q1_templates = registry.list_templates_by_cycle("Q1")
        print(f"   Total: {len(q1_templates)}")
        for t in q1_templates[:5]:
            print(f"   - {t['template_key']:30} | {t['field_count']:3} campos | {t['sheet_name']}")
        if len(q1_templates) > 5:
            print(f"   ... e mais {len(q1_templates) - 5} templates")
        
        # 4. Buscar template específico
        print("\n4️⃣ Buscar template específico (Q1/cronograma):")
        cronograma = registry.get_template("Q1", "cronograma")
        if cronograma:
            print(f"   ✅ Encontrado!")
            print(f"   - Sheet: {cronograma['sheet_name']}")
            print(f"   - Campos: {cronograma['field_count']}")
            print(f"   - Schema path: {cronograma['schema_path']}")
            print(f"   - Image path: {cronograma['image_path']}")
            if 'schema' in cronograma and cronograma['schema']:
                schema = cronograma['schema']
                print(f"   - Sheet dimensions: {schema['sheet_width']:.1f}x{schema['sheet_height']:.1f}px")
                print(f"   - Fields no schema: {len(schema.get('fields', []))}")
        else:
            print("   ❌ Não encontrado")
        
        # 5. Carregar schema de um template
        print("\n5️⃣ Carregar schema JSON (Q1/3_1_persona_01):")
        schema = registry.get_template_schema("Q1", "3_1_persona_01")
        if schema:
            print(f"   ✅ Schema carregado!")
            print(f"   - Template: {schema['template_key']}")
            print(f"   - Sheet: {schema['sheet_name']}")
            print(f"   - Dimensões: {schema['sheet_width']:.1f}x{schema['sheet_height']:.1f}px")
            print(f"   - Total de campos: {len(schema['fields'])}")
            if schema['fields']:
                print(f"   - Primeiro campo:")
                field = schema['fields'][0]
                print(f"     - Key: {field['key']}")
                print(f"     - Label: {field['label']}")
                print(f"     - Cell: {field['cell']}")
                print(f"     - Type: {field['type']}")
                print(f"     - Position: top={field['top']:.1f}, left={field['left']:.1f}")
        else:
            print("   ❌ Schema não encontrado")
        
        # 6. Testar template inexistente
        print("\n6️⃣ Buscar template inexistente (Q99/fake_template):")
        fake = registry.get_template("Q99", "fake_template")
        if fake:
            print("   ❌ Erro: deveria retornar None")
        else:
            print("   ✅ Retornou None como esperado")
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante testes: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = test_registry_endpoints()
    sys.exit(0 if success else 1)
