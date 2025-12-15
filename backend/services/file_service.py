import os
from typing import List
from config import UPLOAD_DIR


def save_file(upload_file) -> str:
    """
    Salva o arquivo enviado no diretório UPLOAD_DIR.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, upload_file.filename)

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
    Remove um arquivo do diretório UPLOAD_DIR.
    """
    file_path = os.path.join(UPLOAD_DIR, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        return True

    return False
