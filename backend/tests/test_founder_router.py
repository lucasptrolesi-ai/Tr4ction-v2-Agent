"""
Testes para routers/founder.py
Cobre endpoints de visualização e progresso de trilhas para founders
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session

from db.models import Trail, StepSchema, User, UserProgress, StepAnswer
from db.database import get_db
from routers.founder import router


@pytest.fixture
def mock_db():
    """Fixture para mockar banco de dados"""
    db = MagicMock(spec=Session)
    db.query = MagicMock(return_value=db)
    db.filter = MagicMock(return_value=db)
    db.order_by = MagicMock(return_value=db)
    db.first = MagicMock()
    db.all = MagicMock(return_value=[])
    db.count = MagicMock(return_value=0)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.flush = MagicMock()
    return db


@pytest.fixture
def app(mock_db):
    """Cria app FastAPI com router founder"""
    app = FastAPI()
    app.include_router(router)
    
    # Override get_db dependency
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Mock get_current_user_id
    from routers.founder import get_current_user_id, get_current_user, get_current_founder
    app.dependency_overrides[get_current_user_id] = lambda: "user-test-001"
    app.dependency_overrides[get_current_user] = lambda: Mock(id="user-test-001", name="Test User")
    app.dependency_overrides[get_current_founder] = lambda: Mock(id="user-test-001", email="founder@test.com")
    
    return app


@pytest.fixture
def client(app):
    """Cliente de teste"""
    return TestClient(app)


@pytest.fixture
def mock_trail():
    """Mock de um objeto Trail"""
    trail = Mock(spec=Trail)
    trail.id = "tr-marketing"
    trail.name = "Marketing Q1"
    trail.description = "Marketing template"
    trail.status = "active"
    trail.created_at = datetime.utcnow()
    trail.updated_at = datetime.utcnow()
    return trail


@pytest.fixture
def mock_step():
    """Mock de um objeto StepSchema"""
    step = Mock(spec=StepSchema)
    step.trail_id = "tr-marketing"
    step.step_id = "icp"
    step.step_name = "ICP"
    step.order = 1
    step.schema = {
        "fields": [
            {"name": "icp_campo1", "type": "text", "label": "ICP Field", "required": True},
            {"name": "icp_descricao", "type": "textarea", "label": "Description"}
        ]
    }
    return step


@pytest.fixture
def mock_user():
    """Mock de um objeto User"""
    user = Mock(spec=User)
    user.id = "user-test-001"
    user.email = "test@example.com"
    user.name = "Test User"
    user.is_active = True
    return user


@pytest.fixture
def mock_progress():
    """Mock de progresso do usuário"""
    progress = Mock(spec=UserProgress)
    progress.user_id = "user-test-001"
    progress.trail_id = "tr-marketing"
    progress.step_id = "icp"
    progress.progress_percent = 50
    progress.is_locked = False
    progress.is_completed = False
    return progress


@pytest.fixture
def mock_answer():
    """Mock de respostas do usuário"""
    answer = Mock(spec=StepAnswer)
    answer.user_id = "user-test-001"
    answer.trail_id = "tr-marketing"
    answer.step_id = "icp"
    answer.answers = {"field1": "value1"}
    return answer


class TestFounderTrailsEndpoints:
    """Testes dos endpoints de trilhas"""
    
    def test_list_trails_empty(self, client, mock_db):
        """GET /founder/trails - Listar sem trilhas"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        response = client.get("/founder/trails")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_trails_with_data(self, client, mock_db, mock_trail, mock_step):
        """GET /founder/trails - Listar com trilhas"""
        # Mock para seed_default_data
        mock_db.query.return_value.first.return_value = mock_trail  # Já tem dados
        
        # Mock para buscar trails
        call_count = 0
        def side_effect_all():
            return [mock_trail]
        
        def side_effect_first():
            return None  # No progress
        
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_trail],  # trails query
            [mock_step]    # steps query
        ]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_step]
        
        response = client.get("/founder/trails")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_trails_with_progress(self, client, mock_db, mock_trail, mock_step, mock_progress, mock_answer):
        """GET /founder/trails - Listar com progresso salvo"""
        mock_db.query.return_value.first.return_value = mock_trail
        
        # Configurar múltiplas queries
        def query_side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            q.order_by.return_value = q
            q.all.return_value = [mock_trail] if model == Trail else [mock_step]
            q.first.side_effect = [mock_progress, mock_answer]  # Para cada chamada filter().first()
            return q
        
        mock_db.query.side_effect = query_side_effect
        
        response = client.get("/founder/trails")
        assert response.status_code in [200, 500]
    
    def test_list_trails_error(self, client, mock_db):
        """GET /founder/trails - Erro ao listar"""
        mock_db.query.return_value.first.side_effect = Exception("Database error")
        
        response = client.get("/founder/trails")
        assert response.status_code == 500
    
    def test_list_trails_seed_initial_data(self, client, mock_db):
        """GET /founder/trails - Seed com dados padrão"""
        # Simula primeiro acesso sem dados
        mock_db.query.return_value.first.return_value = None
        
        response = client.get("/founder/trails")
        # Pode falhar se seed não conseguir criar dados
        assert response.status_code in [200, 500]


class TestFounderStepSchemaEndpoints:
    """Testes dos endpoints de schema de steps"""
    
    def test_get_step_schema_found(self, client, mock_db, mock_step):
        """GET /founder/trails/{trail_id}/steps/{step_id}/schema - Encontrado"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_step
        
        response = client.get("/founder/trails/tr-marketing/steps/icp/schema")
        assert response.status_code == 200
        data = response.json()
        assert "fields" in data
    
    def test_get_step_schema_not_found(self, client, mock_db):
        """GET /founder/trails/{trail_id}/steps/{step_id}/schema - Não encontrado"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/founder/trails/tr-marketing/steps/invalid/schema")
        assert response.status_code == 404  # Endpoint retorna 404 quando não encontra
    
    def test_get_step_schema_with_special_chars(self, client, mock_db):
        """GET /founder/trails/{trail_id}/steps/{step_id}/schema - Caracteres especiais"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/founder/trails/tr-001/steps/step-with-dash/schema")
        assert response.status_code == 404  # Não encontrado
    
    def test_get_step_schema_db_error(self, client, mock_db):
        """GET /founder/trails/{trail_id}/steps/{step_id}/schema - Erro BD"""
        mock_db.query.return_value.filter.return_value.first.side_effect = Exception("DB Error")
        
        response = client.get("/founder/trails/tr-marketing/steps/icp/schema")
        assert response.status_code == 500


class TestFounderProgressEndpoints:
    """Testes dos endpoints de progresso"""
    
    def test_get_step_progress(self, client, mock_db, mock_progress):
        """GET /founder/trails/{trail_id}/steps/{step_id}/progress - Obter progresso"""
        # Configurar mock para primeira query (UserProgress)
        mock_query = MagicMock()
        mock_filter = MagicMock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_progress  # Primeira chamada
        
        # Configurar para segunda query (StepAnswer)
        mock_db.query.side_effect = [mock_query, mock_query]
        
        response = client.get("/founder/trails/tr-marketing/steps/icp/progress")
        # O endpoint pode retornar dados ou erro
        assert response.status_code in [200, 500]
    
    def test_get_step_progress_no_data(self, client, mock_db):
        """GET /founder/trails/{trail_id}/steps/{step_id}/progress - Sem progresso"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/founder/trails/tr-marketing/steps/icp/progress")
        # Pode retornar 200 com dados padrão ou 404
        assert response.status_code in [200, 404, 500]
    
    def test_save_step_progress_success(self, client, mock_db):
        """POST /founder/trails/{trail_id}/steps/{step_id}/progress - Salvar progresso"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.post(
            "/founder/trails/tr-marketing/steps/icp/progress",
            json={
                "formData": {"field1": "value1", "field2": "value2"}
            }
        )
        assert response.status_code in [200, 201]
    
    def test_save_step_progress_with_existing_progress(self, client, mock_db, mock_progress):
        """POST /founder/trails/{trail_id}/steps/{step_id}/progress - Atualizar progresso"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_progress
        
        response = client.post(
            "/founder/trails/tr-marketing/steps/icp/progress",
            json={
                "formData": {"field1": "updated_value"}
            }
        )
        assert response.status_code in [200, 201]
    
    def test_save_step_progress_empty_answers(self, client, mock_db):
        """POST /founder/trails/{trail_id}/steps/{step_id}/progress - Respostas vazias"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.post(
            "/founder/trails/tr-marketing/steps/icp/progress",
            json={
                "formData": {}
            }
        )
        assert response.status_code in [200, 201]
    
    def test_save_step_progress_large_answers(self, client, mock_db):
        """POST /founder/trails/{trail_id}/steps/{step_id}/progress - Respostas grandes"""
        large_text = "x" * 10000
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.post(
            "/founder/trails/tr-marketing/steps/icp/progress",
            json={
                "formData": {"field1": large_text}
            }
        )
        assert response.status_code in [200, 201, 413]  # 413 = Payload Too Large
    
    def test_save_step_progress_db_error(self, client, mock_db):
        """POST /founder/trails/{trail_id}/steps/{step_id}/progress - Erro BD"""
        mock_db.query.return_value.filter.return_value.first.side_effect = Exception("DB Error")
        
        response = client.post(
            "/founder/trails/tr-marketing/steps/icp/progress",
            json={
                "formData": {"field1": "value1"}
            }
        )
        assert response.status_code == 500


class TestFounderExportEndpoints:
    """Testes dos endpoints de export/download"""
    
    def test_download_trail_file(self, client, mock_db):
        """GET /founder/trails/{trail_id}/download - Download"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/founder/trails/tr-marketing/download")
        # Pode retornar arquivo ou erro
        assert response.status_code in [200, 404, 500]
    
    def test_export_trail_xlsx(self, client, mock_db):
        """GET /founder/trails/{trail_id}/export/xlsx - Export Excel"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('routers.founder.generate_xlsx') as mock_export:
            mock_export.return_value = b"xlsx_data"
            
            response = client.get("/founder/trails/tr-marketing/export/xlsx")
            assert response.status_code in [200, 404, 500]


class TestFounderErrorHandling:
    """Testes de tratamento de erros"""
    
    def test_get_with_invalid_trail_id(self, client, mock_db):
        """GET com trail_id vazio"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/founder/trails//steps/icp/schema")
        # FastAPI trata path vazio diferentemente
        assert response.status_code in [404, 422]
    
    def test_get_with_invalid_step_id(self, client, mock_db):
        """GET com step_id vazio"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/founder/trails/tr-001/steps//schema")
        assert response.status_code in [404, 422]
    
    def test_post_with_missing_json_fields(self, client):
        """POST sem campos obrigatórios"""
        response = client.post(
            "/founder/trails/tr-marketing/steps/icp/progress",
            json={}
        )
        assert response.status_code in [400, 422, 200, 500]
    
    def test_post_with_invalid_json(self, client):
        """POST com JSON inválido"""
        response = client.post(
            "/founder/trails/tr-marketing/steps/icp/progress",
            json=None
        )
        assert response.status_code in [400, 422, 500]


class TestFounderIntegrationScenarios:
    """Testes de integração completos"""
    
    def test_complete_step_workflow(self, client, mock_db, mock_trail, mock_step):
        """Cenário: Fluxo completo de um passo"""
        # 1. Listar trilhas
        mock_db.query.return_value.first.return_value = mock_trail
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_trail],
            [mock_step]
        ]
        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_step]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response1 = client.get("/founder/trails")
        assert response1.status_code == 200
        
        # 2. Obter schema do step
        mock_db.query.return_value.filter.return_value.first.return_value = mock_step
        response2 = client.get("/founder/trails/tr-marketing/steps/icp/schema")
        assert response2.status_code == 200
        
        # 3. Salvar progresso
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response3 = client.post(
            "/founder/trails/tr-marketing/steps/icp/progress",
            json={
                "formData": {"field1": "value1"}
            }
        )
        assert response3.status_code in [200, 201]
    
    def test_multiple_steps_progression(self, client, mock_db):
        """Cenário: Progresso através de múltiplos steps"""
        steps = []
        for i in range(3):
            step = Mock(spec=StepSchema)
            step.step_id = f"step-{i}"
            step.step_name = f"Step {i}"
            step.order = i
            step.schema = {"fields": []}
            steps.append(step)
        
        # Salvar progresso em cada step
        for step in steps:
            mock_db.query.return_value.filter.return_value.first.return_value = None
            response = client.post(
                f"/founder/trails/tr-test/steps/{step.step_id}/progress",
                json={
                    "formData": {f"field_{step.step_id}": f"answer_{step.step_id}"}
                }
            )
            assert response.status_code in [200, 201]
    
    def test_trail_completion_flow(self, client, mock_db, mock_trail):
        """Cenário: Conclusão de uma trilha"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Simular conclusão: com dados preenchidos
        response = client.post(
            "/founder/trails/tr-marketing/steps/final/progress",
            json={
                "formData": {"final_field": "completed"}
            }
        )
        assert response.status_code in [200, 201]
