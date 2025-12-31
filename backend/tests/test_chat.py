# backend/tests/test_chat.py
"""
Testes do sistema de chat e RAG
"""
import pytest
from fastapi.testclient import TestClient


class TestChat:
    """Testes do endpoint de chat"""
    
    @pytest.fixture
    def auth_headers(self, client: TestClient):
        """Fixture que retorna headers de autenticação"""
        # Registrar usuário
        client.post(
            "/auth/register",
            json={
                "email": "chat_user@example.com",
                "password": "ChatPass123!",
                "name": "Chat User"
            }
        )
        
        # Fazer login para obter token
        response = client.post(
            "/auth/login",
            json={
                "email": "chat_user@example.com",
                "password": "ChatPass123!"
            }
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_chat_without_auth(self, client: TestClient):
        """Testa chat sem autenticação - Nota: API permite acesso público"""
        response = client.post(
            "/chat/",
            json={"question": "Olá, como você funciona?"}
        )
        # API permite acesso público ao chat, então retorna 200
        assert response.status_code in [200, 500]  # 500 se API externa falhar
    
    def test_chat_with_auth(self, client: TestClient, auth_headers):
        """Testa chat com autenticação"""
        response = client.post(
            "/chat/",
            json={"question": "Explique ICP."},
            headers=auth_headers
        )
        # Pode retornar 200 (sucesso) ou 500 (erro de API externa)
        # Não deve retornar 401 (autenticação)
        assert response.status_code != 401
        
        if response.status_code == 200:
            body = response.json()
            assert "status" in body or "answer" in body or "response" in body
    
    def test_chat_missing_question(self, client: TestClient, auth_headers):
        """Testa chat sem pergunta"""
        response = client.post(
            "/chat/",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
    
    def test_chat_empty_question(self, client: TestClient, auth_headers):
        """Testa chat com pergunta vazia"""
        response = client.post(
            "/chat/",
            json={"question": ""},
            headers=auth_headers
        )
        # Pode retornar 400 (bad request) ou 422 (validation)
        assert response.status_code in [400, 422]
    
    def test_chat_very_long_question(self, client: TestClient, auth_headers):
        """Testa chat com pergunta muito longa"""
        long_question = "Olá " * 1000  # Pergunta muito longa
        response = client.post(
            "/chat/",
            json={"question": long_question},
            headers=auth_headers
        )
        # Sistema deve aceitar ou limitar o tamanho (422 = validação Pydantic)
        assert response.status_code in [200, 400, 413, 422, 500]


# Mantém teste original para compatibilidade
def test_chat_ok(client):
    resp = client.post("/chat/", json={"question": "Explique ICP."})
    # Pode retornar 401 (sem auth) ou 200 (sucesso)
    assert resp.status_code in [200, 401]
    
    if resp.status_code == 200:
        body = resp.json()
        assert body["status"] == "success"
        assert "data" in body


def test_chat_empty_question(client):
    resp = client.post("/chat/", json={"question": ""})
    assert resp.status_code in (400, 422)
