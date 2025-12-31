"""
Exemplo de uso da API de Templates - Simulação de Frontend

Demonstra como founders acessariam templates dinamicamente
"""

import requests
import json

# URL base da API (ajuste conforme ambiente)
BASE_URL = "http://localhost:8000"


def example_founder_workflow():
    """
    Simula workflow de um founder acessando templates
    """
    
    print("=" * 70)
    print("🎯 EXEMPLO: FOUNDER ACESSANDO TEMPLATES DINAMICAMENTE")
    print("=" * 70)
    
    # 1. Listar cycles disponíveis
    print("\n1️⃣ Founder abre página de templates e vê dropdown de cycles:")
    response = requests.get(f"{BASE_URL}/api/templates/cycles")
    if response.status_code == 200:
        data = response.json()['data']
        print(f"   Cycles disponíveis: {data['cycles']}")
    else:
        print(f"   ❌ Erro: {response.status_code}")
        return
    
    # 2. Seleciona Q1 e lista templates
    print("\n2️⃣ Founder seleciona 'Q1' no dropdown:")
    response = requests.get(f"{BASE_URL}/api/templates/Q1")
    if response.status_code == 200:
        data = response.json()['data']
        templates = data['templates']
        print(f"   Total de templates no Q1: {data['total']}")
        print(f"\n   📋 Templates exibidos:")
        for t in templates[:10]:
            print(f"      • {t['sheet_name']:35} ({t['field_count']:3} campos)")
        if len(templates) > 10:
            print(f"      ... e mais {len(templates) - 10} templates")
    else:
        print(f"   ❌ Erro: {response.status_code}")
        return
    
    # 3. Clica em "Persona 01"
    print("\n3️⃣ Founder clica no card 'Persona 01':")
    response = requests.get(f"{BASE_URL}/api/templates/Q1/3_1_persona_01")
    if response.status_code == 200:
        template = response.json()['data']
        schema = template.get('schema', {})
        print(f"   ✅ Template carregado!")
        print(f"   - Nome: {schema.get('title')}")
        print(f"   - Dimensões: {schema.get('sheet_width'):.1f}x{schema.get('sheet_height'):.1f}px")
        print(f"   - Campos: {len(schema.get('fields', []))}")
        print(f"\n   🖼️ Frontend carrega:")
        print(f"      - Background: {template['image_path']}")
        print(f"      - Overlay: {len(schema.get('fields', []))} campos editáveis")
    else:
        print(f"   ❌ Erro: {response.status_code}")
        return
    
    # 4. Visualiza estrutura de um campo
    if schema and schema.get('fields'):
        print("\n4️⃣ Estrutura de um campo (exemplo):")
        field = schema['fields'][0]
        print(f"   ```json")
        print(json.dumps(field, indent=2, ensure_ascii=False))
        print(f"   ```")
        print(f"\n   Frontend renderiza:")
        print(f"   - Input/textarea em position absolute")
        print(f"   - top: {field['top']:.1f}px")
        print(f"   - left: {field['left']:.1f}px")
        print(f"   - width: {field['width']:.1f}px")
        print(f"   - height: {field['height']:.1f}px")
        print(f"   - placeholder: \"{field['label']}\"")
    
    # 5. Simula mudança de cycle
    print("\n5️⃣ Founder muda dropdown para 'Q2' (se existir):")
    response = requests.get(f"{BASE_URL}/api/templates/Q2")
    if response.status_code == 200:
        data = response.json()['data']
        print(f"   ✅ Q2 disponível!")
        print(f"   Total de templates: {data['total']}")
    elif response.status_code == 404:
        print(f"   ℹ️  Q2 ainda não foi carregado por admin")
        print(f"   (Basta admin fazer upload de Template_Q2.xlsx)")
    else:
        print(f"   ❌ Erro: {response.status_code}")
    
    print("\n" + "=" * 70)
    print("✅ WORKFLOW COMPLETO - TOTALMENTE GENÉRICO!")
    print("=" * 70)
    print("\n💡 Observações:")
    print("   - Zero hardcode de cycles no frontend")
    print("   - Templates aparecem automaticamente após upload admin")
    print("   - TemplateCanvas funciona com qualquer template")
    print("   - AI Mentor recebe cycle + template_key dinamicamente")
    print("=" * 70)


def example_admin_upload():
    """
    Simula admin fazendo upload de novo cycle (Q2)
    """
    
    print("\n\n" + "=" * 70)
    print("🔐 EXEMPLO: ADMIN FAZENDO UPLOAD DE TEMPLATE Q2")
    print("=" * 70)
    
    print("\n⚠️  NOTA: Este exemplo requer:")
    print("   1. Token de admin válido")
    print("   2. Arquivo Template_Q2.xlsx")
    print("   3. Backend rodando")
    
    print("\n📝 Comando exemplo:")
    print("""
    curl -X POST "http://localhost:8000/admin/templates/upload" \\
      -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
      -F "file=@Template_Q2.xlsx" \\
      -F "cycle=Q2" \\
      -F "description=Templates Q2 2025"
    """)
    
    print("\n📊 Resultado esperado:")
    print("""
    {
      "success": true,
      "data": {
        "cycle": "Q2",
        "total_sheets": 26,
        "successful": 26,
        "failed": 0,
        "total_fields": 650,
        "registered_in_db": 26,
        "report_path": "backend/TEMPLATE_INGESTION_REPORT_Q2.md"
      }
    }
    """)
    
    print("\n✅ Após upload:")
    print("   - Founders veem 'Q2' no dropdown automaticamente")
    print("   - 26 novos templates disponíveis instantaneamente")
    print("   - Sem necessidade de restart ou deploy")
    
    print("=" * 70)


if __name__ == "__main__":
    try:
        # Exemplo 1: Founder workflow
        example_founder_workflow()
        
        # Exemplo 2: Admin upload
        example_admin_upload()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Backend não está rodando")
        print("   Execute: cd backend && uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
