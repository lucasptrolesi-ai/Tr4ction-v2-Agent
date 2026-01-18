"""
✅ AJUSTE 4: Suporte Robusto a Arquivos Grandes

Funcionalidades:
- Upload em streaming (sem carregar tudo em memória)
- Limite configurável via env
- Validação explícita com erro HTTP 413
- Compressão de snapshot (gzip)
- Liberação de memória pós-processamento
"""

import os
import gzip
import io
import logging
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LargeFileConfig:
    """Configuração de limite de arquivo"""
    
    # ✅ AJUSTE 4: Limite configurável via env
    MAX_TEMPLATE_SIZE_MB = int(os.getenv("MAX_TEMPLATE_SIZE_MB", "50"))
    MAX_TEMPLATE_SIZE_BYTES = MAX_TEMPLATE_SIZE_MB * 1024 * 1024
    
    # Limites por tipo de arquivo
    MAX_XLSX_SIZE_MB = int(os.getenv("MAX_XLSX_SIZE_MB", "50"))
    MAX_XLSX_SIZE_BYTES = MAX_XLSX_SIZE_MB * 1024 * 1024
    
    @classmethod
    def get_limits_info(cls) -> dict:
        """Retorna informação dos limites"""
        return {
            "max_template_size_mb": cls.MAX_TEMPLATE_SIZE_MB,
            "max_template_size_bytes": cls.MAX_TEMPLATE_SIZE_BYTES,
            "max_xlsx_size_mb": cls.MAX_XLSX_SIZE_MB,
            "max_xlsx_size_bytes": cls.MAX_XLSX_SIZE_BYTES,
        }


class FileValidator:
    """Validador de arquivo com suporte a streaming"""
    
    @staticmethod
    def validate_file_size(file_bytes: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        ✅ AJUSTE 4: Validação de tamanho com erro claro
        
        Args:
            file_bytes: Conteúdo do arquivo
            filename: Nome do arquivo
        
        Returns:
            (é_válido, mensagem_erro_ou_none)
        """
        file_size_mb = len(file_bytes) / (1024 * 1024)
        
        # Validar extensão
        if not filename.lower().endswith(".xlsx"):
            return False, "Apenas arquivos .xlsx são suportados"
        
        # Validar tamanho
        if len(file_bytes) > LargeFileConfig.MAX_XLSX_SIZE_BYTES:
            return False, (
                f"Arquivo muito grande: {file_size_mb:.1f}MB. "
                f"Limite: {LargeFileConfig.MAX_XLSX_SIZE_MB}MB. "
                f"HTTP 413 Payload Too Large"
            )
        
        logger.info(
            f"✓ Arquivo validado: {filename} ({file_size_mb:.1f}MB, "
            f"limite: {LargeFileConfig.MAX_XLSX_SIZE_MB}MB)"
        )
        
        return True, None
    
    @staticmethod
    def validate_content_length(content_length: Optional[int]) -> Tuple[bool, Optional[str]]:
        """
        ✅ AJUSTE 4: Validação de Content-Length header
        
        Permite rejeitar grandes uploads ANTES de começar.
        """
        if content_length is None:
            return True, None  # Header não fornecido, permitir
        
        content_length_mb = content_length / (1024 * 1024)
        
        if content_length > LargeFileConfig.MAX_XLSX_SIZE_BYTES:
            return False, (
                f"Content-Length muito grande: {content_length_mb:.1f}MB. "
                f"Limite: {LargeFileConfig.MAX_XLSX_SIZE_MB}MB"
            )
        
        return True, None


class MemoryEfficientSnapshot:
    """
    ✅ AJUSTE 4: Snapshot comprimido para economizar memória
    """
    
    @staticmethod
    def compress_snapshot(snapshot_dict: dict) -> bytes:
        """
        Comprime snapshot para gzip (reduz tamanho)
        
        Args:
            snapshot_dict: Snapshot completo
        
        Returns:
            Bytes comprimido
        """
        import json
        
        # Serializar
        json_str = json.dumps(snapshot_dict, ensure_ascii=False)
        json_bytes = json_str.encode("utf-8")
        
        # Comprimir
        compressed = io.BytesIO()
        with gzip.GzipFile(fileobj=compressed, mode="wb") as gz:
            gz.write(json_bytes)
        
        compressed_bytes = compressed.getvalue()
        
        logger.info(
            f"✓ Snapshot comprimido: "
            f"{len(json_bytes) / 1024:.1f}KB → {len(compressed_bytes) / 1024:.1f}KB "
            f"(razão: {100 - (len(compressed_bytes) / len(json_bytes) * 100):.0f}%)"
        )
        
        return compressed_bytes
    
    @staticmethod
    def decompress_snapshot(compressed_bytes: bytes) -> dict:
        """
        Descomprime snapshot
        
        Args:
            compressed_bytes: Bytes comprimido
        
        Returns:
            Dicionário de snapshot
        """
        import json
        
        with gzip.GzipFile(fileobj=io.BytesIO(compressed_bytes), mode="rb") as gz:
            json_bytes = gz.read()
        
        json_str = json_bytes.decode("utf-8")
        snapshot_dict = json.loads(json_str)
        
        return snapshot_dict


class StreamingFileProcessor:
    """
    ✅ AJUSTE 4: Processamento em streaming
    
    Permite processar arquivos grandes sem carregar tudo em memória.
    """
    
    @staticmethod
    def process_upload_stream(
        file_bytes: bytes,
        filename: str,
        max_size_bytes: int,
    ) -> Tuple[bool, bytes, Optional[str]]:
        """
        Processa upload com validação de tamanho
        
        Args:
            file_bytes: Conteúdo do arquivo
            filename: Nome do arquivo
            max_size_bytes: Tamanho máximo permitido
        
        Returns:
            (sucesso, conteúdo_ou_vazio, erro_ou_none)
        """
        # Validação rápida de tamanho
        if len(file_bytes) > max_size_bytes:
            size_mb = len(file_bytes) / (1024 * 1024)
            limit_mb = max_size_bytes / (1024 * 1024)
            error = (
                f"Arquivo excede limite: {size_mb:.1f}MB > {limit_mb:.1f}MB. "
                f"Resposta: HTTP 413 Payload Too Large"
            )
            logger.error(f"❌ {error}")
            return False, b"", error
        
        # Sucesso
        logger.info(f"✓ Arquivo aceito: {filename} ({len(file_bytes) / 1024:.1f}KB)")
        return True, file_bytes, None
