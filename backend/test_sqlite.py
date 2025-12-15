"""
Script de teste para verificar se a persistência SQLite está funcionando
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_founder_trails():
    """Testa GET /founder/trails"""
    print("\n=== Testando GET /founder/trails ===")
    try:
        r = requests.get(f"{BASE_URL}/founder/trails", timeout=5)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Trilhas encontradas: {len(data)}")
        for trail in data:
            print(f"  - {trail['id']}: {trail['name']} ({len(trail.get('steps', []))} steps)")
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_save_progress():
    """Testa POST /founder/trails/.../progress"""
    print("\n=== Testando POST (salvar progresso) ===")
    try:
        r = requests.post(
            f"{BASE_URL}/founder/trails/q1-marketing/steps/icp/progress",
            json={"formData": {"campo1": "Valor teste", "campo2": "Outro valor"}},
            timeout=5
        )
        print(f"Status: {r.status_code}")
        print(f"Resposta: {r.json()}")
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_get_progress():
    """Testa GET /founder/trails/.../progress"""
    print("\n=== Testando GET (ler progresso salvo) ===")
    try:
        r = requests.get(
            f"{BASE_URL}/founder/trails/q1-marketing/steps/icp/progress",
            timeout=5
        )
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Dados salvos: {data.get('formData', {})}")
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_admin_trails():
    """Testa GET /admin/trails"""
    print("\n=== Testando GET /admin/trails ===")
    try:
        r = requests.get(f"{BASE_URL}/admin/trails", timeout=5)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Trilhas admin: {len(data)}")
        for trail in data:
            print(f"  - {trail['id']}: {trail['name']} (status: {trail.get('status', 'N/A')})")
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TESTE DE PERSISTÊNCIA SQLITE")
    print("=" * 50)
    
    results = []
    results.append(("GET /founder/trails", test_founder_trails()))
    results.append(("POST progress", test_save_progress()))
    results.append(("GET progress", test_get_progress()))
    results.append(("GET /admin/trails", test_admin_trails()))
    
    print("\n" + "=" * 50)
    print("RESUMO DOS TESTES")
    print("=" * 50)
    for name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {status} - {name}")
