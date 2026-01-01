import os
import re
from typing import List
from pathlib import Path
from config import UPLOADS_DIR as UPLOAD_DIR  # UPLOADS_DIR do config


def save_file(upload_file) -> str:
    """
    Salva o arquivo enviado no diretório UPLOAD_DIR com validação de segurança.
    
    Proteções implementadas:
    - Path traversal prevention
    - Extension whitelist
    - Filename sanitization
    - Path validation
    """
    # 1. Sanitiza filename removendo path components
    safe_filename = Path(upload_file.filename).name
    
    # 2. Valida extensão contra whitelist
    allowed_extensions = {'.pdf', '.pptx', '.docx', '.txt', '.xlsx', '.xls', '.csv'}
    file_ext = Path(safe_filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise ValueError(f"Extension not allowed: {file_ext}. Allowed: {', '.join(allowed_extensions)}")
    
    # 3. Valida caracteres perigosos
    if any(c in safe_filename for c in ['..', '/', '\\', '\0', '\n', '\r']):
        raise ValueError(f"Invalid characters in filename: {safe_filename}")
    
    # 4. Valida tamanho do nome do arquivo
    if len(safe_filename) > 255:
        raise ValueError("Filename too long (max 255 characters)")
    
    # 5. Valida caracteres permitidos (alfanuméricos, underscore, hífen, ponto)
    if not re.match(r'^[\w\-. ]+$', safe_filename):
        raise ValueError(f"Filename contains invalid characters: {safe_filename}")
    
    # 6. Garante que o diretório existe
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # 7. Constrói path e valida que está dentro de UPLOAD_DIR (path traversal protection)
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    resolved_path = os.path.realpath(file_path)
    resolved_upload_dir = os.path.realpath(UPLOAD_DIR)
    
    if not resolved_path.startswith(resolved_upload_dir):
        raise ValueError("Path traversal attempt detected")
    
    # 8. Salva arquivo de forma segura
    with open(file_path, "wb") as f:
        f.write(upload_file.file.read())

    return file_path


def list_files() -> List[str]:
    """
    Lista todos os arquivos no diretório UPLOAD_DIR.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    return sorted(os.listdir(UPLOAD_DIR))


def delete_file(filename: str) -> bool:
    """
    Remove um arquivo do diretório UPLOAD_DIR com validação de segurança.
    
    Proteções implementadas:
    - Path traversal prevention
    - Directory boundary validation
    """
    # 1. Sanitiza filename removendo path components
    safe_filename = Path(filename).name
    
    # 2. Valida caracteres perigosos
    if any(c in safe_filename for c in ['..', '/', '\\', '\0']):
        raise ValueError(f"Invalid characters in filename: {safe_filename}")
    
    # 3. Constrói path e valida que está dentro de UPLOAD_DIR
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    resolved_path = os.path.realpath(file_path)
    resolved_upload_dir = os.path.realpath(UPLOAD_DIR)
    
    if not resolved_path.startswith(resolved_upload_dir):
        raise ValueError("Path traversal attempt detected")
    
    # 4. Remove arquivo se existir
    if os.path.exists(file_path):
        os.remove(file_path)
        return True

    return False
