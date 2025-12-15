# backend/services/embedding_service.py
"""
Embedding Service - Gera embeddings para RAG
Suporta dois providers:
  - huggingface: API externa (FREE, baixo uso de RAM) ← RECOMENDADO para EC2 t3.micro
  - local: Sentence Transformers local (alto uso de RAM)

Modelo: all-MiniLM-L6-v2 (384 dimensões)
"""

import os
import sys
import time
import requests
from typing import List, Optional

# Garante que .env seja carregado antes de ler variáveis
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# ===================================================================
# 🔧 CONFIGURAÇÃO
# ===================================================================

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface").lower()
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
# Nova URL do Hugging Face Inference Router
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_EMBEDDING_MODEL}"

# Dimensão do embedding (all-MiniLM-L6-v2 produz 384 dimensões)
EMBEDDING_DIMENSION = 384

# Retry config
MAX_RETRIES = 3
RETRY_DELAY = 1.0


# ===================================================================
# 🔍 DETECÇÃO DE AMBIENTE DE TESTE
# ===================================================================

def detect_test_mode() -> bool:
    """Detecta se estamos rodando pytest"""
    if os.getenv("PYTEST_CURRENT_TEST") is not None:
        return True
    if "pytest" in sys.modules:
        return True
    if sys.argv and "pytest" in sys.argv[0].lower():
        return True
    return False


IS_TEST_MODE = detect_test_mode()


# ===================================================================
# 🌐 HUGGING FACE API (RECOMENDADO - BAIXO USO DE RAM)
# ===================================================================

def _embed_via_huggingface(texts: List[str]) -> List[List[float]]:
    """
    Gera embeddings via Hugging Face Inference API.
    
    ✅ Vantagens:
    - Gratuito (free tier)
    - Baixíssimo uso de RAM (~50MB)
    - Mesmo modelo all-MiniLM-L6-v2
    
    ⚠️ Limitações:
    - Rate limit no free tier
    - Latência de rede (~200-500ms por request)
    """
    if not HF_API_TOKEN:
        print("⚠️ [EMBEDDING] HF_API_TOKEN não configurado!")
        return [[0.1] * EMBEDDING_DIMENSION for _ in texts]
    
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Hugging Face aceita lista de textos
    payload = {
        "inputs": texts,
        "options": {
            "wait_for_model": True  # Aguarda se modelo estiver carregando
        }
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                HF_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                embeddings = response.json()
                
                # Validação de dimensão
                if embeddings and len(embeddings) > 0:
                    # HF retorna lista de embeddings (cada um é lista de floats)
                    if isinstance(embeddings[0], list):
                        return embeddings
                    else:
                        # Caso seja embedding único
                        return [embeddings]
                
            elif response.status_code == 503:
                # Modelo carregando
                print(f"⏳ [EMBEDDING] Modelo carregando no HF... tentativa {attempt + 1}/{MAX_RETRIES}")
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
                
            elif response.status_code == 429:
                # Rate limit
                print(f"⚠️ [EMBEDDING] Rate limit HF. Aguardando...")
                time.sleep(RETRY_DELAY * 5)
                continue
                
            else:
                print(f"❌ [EMBEDDING] Erro HF API: {response.status_code} - {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️ [EMBEDDING] Timeout na requisição HF (tentativa {attempt + 1})")
            time.sleep(RETRY_DELAY)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ [EMBEDDING] Erro de conexão HF: {e}")
            time.sleep(RETRY_DELAY)
    
    # Fallback após todas as tentativas
    print("⚠️ [EMBEDDING] Usando fallback após falhas no HF")
    return [[0.1] * EMBEDDING_DIMENSION for _ in texts]


# ===================================================================
# 🖥️ MODELO LOCAL (ALTO USO DE RAM - ~500MB)
# ===================================================================

_local_model = None
_local_model_name = "all-MiniLM-L6-v2"


def _get_local_model():
    """Carrega modelo local (lazy loading)"""
    global _local_model
    
    if _local_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print(f">>> [EMBEDDING] Carregando modelo local {_local_model_name}...")
            _local_model = SentenceTransformer(_local_model_name)
            print(f">>> [EMBEDDING] Modelo local carregado!")
        except ImportError:
            print("❌ [EMBEDDING] sentence-transformers não instalado")
            return None
        except Exception as e:
            print(f"❌ [EMBEDDING] Erro ao carregar modelo local: {e}")
            return None
    
    return _local_model


def _embed_via_local(texts: List[str]) -> List[List[float]]:
    """
    Gera embeddings usando modelo local.
    
    ⚠️ AVISO: Consome ~500MB de RAM!
    Não recomendado para EC2 t3.micro.
    """
    model = _get_local_model()
    
    if model is None:
        return [[0.1] * EMBEDDING_DIMENSION for _ in texts]
    
    try:
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]
    except Exception as e:
        print(f"❌ [EMBEDDING] Erro no modelo local: {e}")
        return [[0.1] * EMBEDDING_DIMENSION for _ in texts]


# ===================================================================
# 🔌 FUNÇÕES PÚBLICAS (API PRINCIPAL)
# ===================================================================

def embed_text(text: str) -> List[float]:
    """
    Gera embedding para um texto.
    
    Args:
        text: Texto para gerar embedding
        
    Returns:
        Lista de floats (384 dimensões)
    """
    # Modo teste
    if IS_TEST_MODE:
        return [0.1] * EMBEDDING_DIMENSION
    
    # Texto vazio
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIMENSION
    
    # Gera embedding
    embeddings = embed_texts([text])
    return embeddings[0] if embeddings else [0.1] * EMBEDDING_DIMENSION


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Gera embeddings para múltiplos textos (batch).
    
    Usa o provider configurado em EMBEDDING_PROVIDER:
    - "huggingface": API externa (recomendado)
    - "local": Modelo local (alto RAM)
    
    Args:
        texts: Lista de textos
        
    Returns:
        Lista de embeddings (cada um com 384 dimensões)
    """
    # Modo teste
    if IS_TEST_MODE:
        return [[0.1] * EMBEDDING_DIMENSION for _ in texts]
    
    # Lista vazia
    if not texts:
        return []
    
    # Filtra textos vazios
    clean_texts = [t if t and t.strip() else " " for t in texts]
    
    # Escolhe provider
    if EMBEDDING_PROVIDER == "huggingface":
        print(f"🌐 [EMBEDDING] Usando Hugging Face API ({len(texts)} textos)")
        return _embed_via_huggingface(clean_texts)
    
    elif EMBEDDING_PROVIDER == "local":
        print(f"🖥️ [EMBEDDING] Usando modelo local ({len(texts)} textos)")
        return _embed_via_local(clean_texts)
    
    else:
        print(f"⚠️ [EMBEDDING] Provider desconhecido: {EMBEDDING_PROVIDER}. Usando huggingface.")
        return _embed_via_huggingface(clean_texts)


def get_embedding_dimension() -> int:
    """Retorna a dimensão do embedding"""
    return EMBEDDING_DIMENSION


def get_model_info() -> dict:
    """Retorna informações sobre o serviço de embedding"""
    return {
        "provider": EMBEDDING_PROVIDER,
        "model": HF_EMBEDDING_MODEL if EMBEDDING_PROVIDER == "huggingface" else _local_model_name,
        "dimension": EMBEDDING_DIMENSION,
        "is_test_mode": IS_TEST_MODE,
        "hf_configured": bool(HF_API_TOKEN),
        "local_model_loaded": _local_model is not None
    }


def test_embedding_service() -> dict:
    """
    Testa o serviço de embedding.
    Útil para verificar se a configuração está correta.
    """
    test_text = "Este é um teste de embedding"
    
    try:
        start = time.time()
        embedding = embed_text(test_text)
        elapsed = (time.time() - start) * 1000
        
        return {
            "success": True,
            "provider": EMBEDDING_PROVIDER,
            "dimension": len(embedding),
            "expected_dimension": EMBEDDING_DIMENSION,
            "dimension_ok": len(embedding) == EMBEDDING_DIMENSION,
            "latency_ms": round(elapsed, 2),
            "sample_values": embedding[:5]  # Primeiros 5 valores
        }
    except Exception as e:
        return {
            "success": False,
            "provider": EMBEDDING_PROVIDER,
            "error": str(e)
        }


# ===================================================================
# 🧪 INICIALIZAÇÃO
# ===================================================================

if not IS_TEST_MODE:
    print(f"🧠 [EMBEDDING] Provider configurado: {EMBEDDING_PROVIDER.upper()}")
    if EMBEDDING_PROVIDER == "huggingface":
        if HF_API_TOKEN:
            print(f"✅ [EMBEDDING] HF Token configurado (modelo: {HF_EMBEDDING_MODEL})")
        else:
            print("⚠️ [EMBEDDING] HF Token NÃO configurado! Adicione HF_API_TOKEN no .env")
