"""
Template Storage Service - Armazenamento versionado de templates
================================================================

RESPONSABILIDADE:
Persistir templates Excel + snapshots + assets de forma organizada,
versionada e auditável.

ESTRUTURA:
{TEMPLATE_STORAGE_PATH}/
  {template_key}/
    {cycle}/
      {hash}/
        original.xlsx
        template.snapshot.json.gz
        assets/
          image_0.png
          image_1.png
        assets.manifest.json

GARANTIAS:
- Idempotência por hash SHA-256
- Compressão gzip de snapshots
- Manifesto de assets
- Paths absolutos retornados
"""

from __future__ import annotations
import os
import gzip
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TemplateStorageService:
    """
    Serviço de armazenamento de templates
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Args:
            base_path: Caminho base para storage. Se None, usa env ou default.
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Buscar de env ou usar default
            env_path = os.getenv("TEMPLATE_STORAGE_PATH")
            if env_path:
                self.base_path = Path(env_path)
            else:
                # Fallback: DATA_DIR/templates_storage
                data_dir = os.getenv("DATA_DIR", "backend/data")
                self.base_path = Path(data_dir) / "templates_storage"
        
        # Criar base se não existir
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Template storage: {self.base_path.absolute()}")

    def save(
        self,
        file_name: str,
        file_bytes: bytes,
        snapshot_dict: Dict[str, Any],
        assets: List[Dict[str, Any]],
        template_key: str,
        cycle: str,
    ) -> Dict[str, Any]:
        """
        Salva template completo com versionamento por hash
        
        Args:
            file_name: Nome original do arquivo
            file_bytes: Conteúdo binário do .xlsx
            snapshot_dict: Snapshot JSON
            assets: Lista de assets (imagens)
            template_key: Chave do template
            cycle: Cycle FCJ
            
        Returns:
            Dict com:
            - paths: Dict com caminhos absolutos
            - hash: SHA-256 do arquivo
            - size: Tamanho em bytes
        """
        # Computar hash
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        
        # Estrutura de diretórios
        version_dir = self.base_path / template_key / cycle / file_hash
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Salvar original
        original_path = version_dir / "original.xlsx"
        with open(original_path, "wb") as f:
            f.write(file_bytes)
        
        # 2. Salvar snapshot compactado
        snapshot_path = version_dir / "template.snapshot.json.gz"
        with gzip.open(snapshot_path, "wt", encoding="utf-8") as f:
            json.dump(snapshot_dict, f, indent=2, ensure_ascii=False)
        
        # 3. Salvar assets
        assets_dir = version_dir / "assets"
        assets_manifest = []
        
        if assets:
            assets_dir.mkdir(exist_ok=True)
            
            for asset in assets:
                sheet_name = asset.get("sheet_name")
                index = asset.get("index")
                format_ext = asset.get("format", "png").lower()
                binary = asset.get("binary")
                
                if not binary:
                    continue
                
                filename = f"{sheet_name}_image_{index}.{format_ext}"
                asset_path = assets_dir / filename
                
                with open(asset_path, "wb") as f:
                    f.write(binary)
                
                assets_manifest.append({
                    "filename": filename,
                    "sheet": sheet_name,
                    "index": index,
                    "format": format_ext,
                    "size": len(binary),
                    "path": str(asset_path.relative_to(self.base_path)),
                })
        
        # 4. Salvar manifest de assets
        manifest_path = version_dir / "assets.manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(assets_manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(
            f"✓ Template salvo: {template_key}/{cycle}/{file_hash[:8]} "
            f"({len(assets)} assets, {len(file_bytes)} bytes)"
        )
        
        return {
            "paths": {
                "original_path": str(original_path.absolute()),
                "snapshot_path": str(snapshot_path.absolute()),
                "assets_manifest_path": str(manifest_path.absolute()) if assets else None,
                "assets_dir": str(assets_dir.absolute()) if assets else None,
            },
            "hash": file_hash,
            "size": len(file_bytes),
            "assets_count": len(assets_manifest),
        }

    def load_snapshot(self, snapshot_path: str) -> Dict[str, Any]:
        """
        Carrega snapshot descompactado
        
        Args:
            snapshot_path: Caminho absoluto do snapshot.json.gz
            
        Returns:
            Snapshot dict
        """
        with gzip.open(snapshot_path, "rt", encoding="utf-8") as f:
            return json.load(f)

    def exists(self, template_key: str, cycle: str, file_hash: str) -> bool:
        """
        Verifica se versão já existe
        
        Returns:
            True se existe
        """
        version_dir = self.base_path / template_key / cycle / file_hash
        original_path = version_dir / "original.xlsx"
        return original_path.exists()
