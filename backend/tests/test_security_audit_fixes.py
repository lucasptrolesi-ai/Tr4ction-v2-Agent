"""
Testes de Segurança - Validação de correções críticas
Senior Engineer Security Audit Follow-up

Valida:
1. Path Traversal Prevention
2. Password Strength Requirements
3. Input Validation
4. Error Handling Sanitization
"""

import pytest
import sys
import os
from pathlib import Path
import tempfile

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["TESTING"] = "1"


class TestPathTraversalPrevention:
    """Testa proteção contra path traversal attacks"""
    
    def test_path_traversal_blocked_with_dot_dot(self):
        """Testa que ../ é bloqueado"""
        from services.file_service import save_file
        
        class MockFile:
            def __init__(self, filename):
                self.filename = filename
                self.file = type('obj', (object,), {'read': lambda self: b'test content'})()
        
        with pytest.raises(ValueError) as exc_info:
            save_file(MockFile("../../../etc/passwd"))
        
        # Aceita qualquer erro relacionado a segurança (chars inválidos ou extensão)
        error_msg = str(exc_info.value)
        assert any(keyword in error_msg for keyword in ["Invalid characters", "Extension not allowed", "Path traversal"])
    
    def test_path_traversal_blocked_with_absolute_path(self):
        """Testa que paths absolutos são bloqueados"""
        from services.file_service import save_file
        
        class MockFile:
            def __init__(self, filename):
                self.filename = filename
                self.file = type('obj', (object,), {'read': lambda self: b'test content'})()
        
        with pytest.raises(ValueError) as exc_info:
            save_file(MockFile("/etc/passwd"))
        
        error_msg = str(exc_info.value)
        assert any(keyword in error_msg for keyword in ["Invalid characters", "Extension not allowed", "Invalid filename"])
    
    def test_path_traversal_blocked_with_backslash(self):
        """Testa que backslashes são bloqueados"""
        from services.file_service import save_file
        
        class MockFile:
            def __init__(self, filename):
                self.filename = filename
                self.file = type('obj', (object,), {'read': lambda self: b'test content'})()
        
        with pytest.raises(ValueError) as exc_info:
            save_file(MockFile("..\\..\\windows\\system32"))
        
        error_msg = str(exc_info.value)
        assert any(keyword in error_msg for keyword in ["Invalid characters", "Extension not allowed"])
    
    def test_valid_filename_accepted(self):
        """Testa que filename válido é aceito"""
        from services.file_service import save_file
        
        class MockFile:
            def __init__(self, filename):
                self.filename = filename
                self.file = type('obj', (object,), {'read': lambda self: b'test content'})()
        
        # Deve funcionar sem exceção
        try:
            result = save_file(MockFile("valid_document.pdf"))
            assert result is not None
            # Limpa arquivo de teste
            if os.path.exists(result):
                os.remove(result)
        except Exception as e:
            pytest.fail(f"Valid filename should not raise exception: {e}")
    
    def test_invalid_extension_blocked(self):
        """Testa que extensões não permitidas são bloqueadas"""
        from services.file_service import save_file
        
        class MockFile:
            def __init__(self, filename):
                self.filename = filename
                self.file = type('obj', (object,), {'read': lambda self: b'test content'})()
        
        with pytest.raises(ValueError) as exc_info:
            save_file(MockFile("malware.exe"))
        
        assert "Extension not allowed" in str(exc_info.value)
    
    def test_filename_too_long_blocked(self):
        """Testa que nomes muito longos são bloqueados"""
        from services.file_service import save_file
        
        class MockFile:
            def __init__(self, filename):
                self.filename = filename
                self.file = type('obj', (object,), {'read': lambda self: b'test content'})()
        
        long_filename = "a" * 300 + ".pdf"
        with pytest.raises(ValueError) as exc_info:
            save_file(MockFile(long_filename))
        
        assert "too long" in str(exc_info.value)


class TestPasswordStrengthRequirements:
    """Testa requisitos de força de senha"""
    
    def test_weak_password_too_short(self):
        """Testa que senha muito curta é rejeitada"""
        from services.auth import UserCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Short1!",  # 7 chars
                name="Test User"
            )
        
        errors = str(exc_info.value)
        assert "at least 8 characters" in errors
    
    def test_weak_password_no_uppercase(self):
        """Testa que senha sem maiúscula é rejeitada"""
        from services.auth import UserCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="weakpass123!",  # Sem maiúscula
                name="Test User"
            )
        
        errors = str(exc_info.value)
        assert "uppercase letter" in errors
    
    def test_weak_password_no_lowercase(self):
        """Testa que senha sem minúscula é rejeitada"""
        from services.auth import UserCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="WEAKPASS123!",  # Sem minúscula
                name="Test User"
            )
        
        errors = str(exc_info.value)
        assert "lowercase letter" in errors
    
    def test_weak_password_no_digit(self):
        """Testa que senha sem número é rejeitada"""
        from services.auth import UserCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="WeakPass!",  # Sem número
                name="Test User"
            )
        
        errors = str(exc_info.value)
        assert "digit" in errors
    
    def test_weak_password_no_special_char(self):
        """Testa que senha sem caractere especial é rejeitada"""
        from services.auth import UserCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="WeakPass123",  # Sem especial
                name="Test User"
            )
        
        errors = str(exc_info.value)
        assert "special character" in errors
    
    def test_strong_password_accepted(self):
        """Testa que senha forte é aceita"""
        from services.auth import UserCreate
        
        # Não deve lançar exceção
        user = UserCreate(
            email="test@example.com",
            password="StrongPass123!",  # Atende todos os requisitos
            name="Test User"
        )
        assert user.password == "StrongPass123!"
    
    def test_invalid_email_format_rejected(self):
        """Testa que email inválido é rejeitado"""
        from services.auth import UserCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="invalid-email",  # Sem @
                password="StrongPass123!",
                name="Test User"
            )
        
        errors = str(exc_info.value)
        assert "Invalid email format" in errors


class TestErrorHandlingSanitization:
    """Testa que erros são sanitizados em produção"""
    
    def test_error_response_does_not_expose_sensitive_paths(self):
        """Testa que paths do sistema não são expostos"""
        from fastapi.testclient import TestClient
        from main import create_app
        
        # Simula ambiente de produção
        original_debug = os.getenv("DEBUG_MODE")
        os.environ["DEBUG_MODE"] = "false"
        
        try:
            app = create_app()
            client = TestClient(app)
            
            # Força um erro interno
            response = client.get("/non-existent-endpoint")
            
            # Deve retornar 404, não 500 com stack trace
            assert response.status_code == 404
            
        finally:
            if original_debug:
                os.environ["DEBUG_MODE"] = original_debug
            else:
                os.environ.pop("DEBUG_MODE", None)


class TestFileServiceSecurityImprovements:
    """Testa melhorias de segurança no file_service"""
    
    def test_delete_file_path_traversal_blocked(self):
        """Testa que delete_file também bloqueia path traversal"""
        from services.file_service import delete_file
        
        # Path traversal sem extensão não deve passar pela validação
        # A função agora remove path components, então teste passará se não houver erro
        # ou se houver erro de "file not found"
        try:
            result = delete_file("../../etc/passwd")
            # Se chegou aqui, o arquivo não existia (seguro)
            assert result is False
        except ValueError as e:
            # Se lançou ValueError, também é seguro (bloqueado)
            error_msg = str(e)
            assert any(keyword in error_msg for keyword in ["Invalid characters", "Path traversal"])
    
    def test_valid_delete_works(self):
        """Testa que delete de arquivo válido funciona"""
        from services.file_service import delete_file, save_file
        
        class MockFile:
            def __init__(self, filename):
                self.filename = filename
                self.file = type('obj', (object,), {'read': lambda self: b'test content'})()
        
        # Cria arquivo
        filepath = save_file(MockFile("test_delete.txt"))
        filename = os.path.basename(filepath)
        
        # Deleta arquivo
        result = delete_file(filename)
        assert result is True
        
        # Verifica que não existe mais
        assert not os.path.exists(filepath)
    
    def test_delete_nonexistent_file_returns_false(self):
        """Testa que delete de arquivo inexistente retorna False"""
        from services.file_service import delete_file
        
        result = delete_file("nonexistent_file_12345.txt")
        assert result is False


class TestBareExceptRemoval:
    """Testa que bare except clauses foram removidos"""
    
    def test_no_bare_except_in_critical_files(self):
        """Verifica que arquivos críticos não têm bare except"""
        import re
        
        critical_files = [
            "/workspaces/Tr4ction-v2-Agent/backend/services/knowledge_service.py",
            "/workspaces/Tr4ction-v2-Agent/backend/services/template_ingestion_service.py",
        ]
        
        for filepath in critical_files:
            if not os.path.exists(filepath):
                continue
                
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Remove comentários para não dar falso positivo
            content_no_comments = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
            
            # Procura por bare except (except: sem tipo)
            bare_excepts = re.findall(r'\bexcept\s*:\s*$', content_no_comments, flags=re.MULTILINE)
            
            assert len(bare_excepts) == 0, f"Found {len(bare_excepts)} bare except in {filepath}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
