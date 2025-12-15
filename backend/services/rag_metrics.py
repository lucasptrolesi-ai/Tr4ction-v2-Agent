# backend/services/rag_metrics.py
"""
Serviço de Métricas do RAG
Coleta e armazena métricas de uso para análise e otimização.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading

# Diretório para persistir métricas
METRICS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "metrics")
os.makedirs(METRICS_DIR, exist_ok=True)

METRICS_FILE = os.path.join(METRICS_DIR, "rag_metrics.json")
QUERIES_LOG_FILE = os.path.join(METRICS_DIR, "queries_log.jsonl")

# Lock para thread safety
_metrics_lock = threading.Lock()


# ======================================================
# Estruturas de Dados
# ======================================================

@dataclass
class QueryMetric:
    """Métrica de uma query individual"""
    query_id: str
    timestamp: str
    question: str
    trail_id: Optional[str]
    step_id: Optional[str]
    user_id: Optional[str]
    chunks_retrieved: int
    avg_similarity: float
    response_time_ms: int
    tokens_used: int
    had_context: bool
    sources_used: List[str]


@dataclass
class RAGMetrics:
    """Métricas agregadas do RAG"""
    total_queries: int = 0
    queries_with_context: int = 0
    queries_without_context: int = 0
    avg_response_time_ms: float = 0.0
    avg_chunks_retrieved: float = 0.0
    avg_similarity_score: float = 0.0
    total_tokens_used: int = 0
    
    # Por período
    queries_today: int = 0
    queries_this_week: int = 0
    queries_this_month: int = 0
    
    # Por trilha
    queries_by_trail: Dict[str, int] = None
    
    # Top queries (mais frequentes)
    top_queries: List[Dict] = None
    
    # Documentos mais usados
    top_documents: List[Dict] = None
    
    def __post_init__(self):
        if self.queries_by_trail is None:
            self.queries_by_trail = {}
        if self.top_queries is None:
            self.top_queries = []
        if self.top_documents is None:
            self.top_documents = []


# ======================================================
# Classe Principal do Serviço
# ======================================================

class RAGMetricsService:
    """Serviço singleton para coleta de métricas"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not RAGMetricsService._initialized:
            self.metrics = self._load_metrics()
            self.query_counts = defaultdict(int)
            self.doc_usage = defaultdict(int)
            RAGMetricsService._initialized = True
    
    # ======================================================
    # Persistência
    # ======================================================
    
    def _load_metrics(self) -> Dict[str, Any]:
        """Carrega métricas do disco"""
        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Erro ao carregar métricas: {e}")
        
        return {
            "total_queries": 0,
            "queries_with_context": 0,
            "queries_without_context": 0,
            "total_response_time_ms": 0,
            "total_chunks_retrieved": 0,
            "total_similarity_score": 0.0,
            "total_tokens_used": 0,
            "queries_by_trail": {},
            "queries_by_day": {},
            "query_counts": {},
            "doc_usage": {},
            "last_updated": None
        }
    
    def _save_metrics(self):
        """Salva métricas no disco"""
        with _metrics_lock:
            self.metrics["last_updated"] = datetime.utcnow().isoformat()
            try:
                with open(METRICS_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.metrics, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️ Erro ao salvar métricas: {e}")
    
    def _log_query(self, metric: QueryMetric):
        """Loga query individual em arquivo JSONL"""
        try:
            with open(QUERIES_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(metric), ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️ Erro ao logar query: {e}")
    
    # ======================================================
    # Registro de Métricas
    # ======================================================
    
    def record_query(
        self,
        question: str,
        chunks_retrieved: int,
        avg_similarity: float,
        response_time_ms: int,
        tokens_used: int = 0,
        trail_id: Optional[str] = None,
        step_id: Optional[str] = None,
        user_id: Optional[str] = None,
        sources: Optional[List[str]] = None
    ):
        """
        Registra uma query no sistema de métricas.
        
        Args:
            question: Pergunta feita pelo usuário
            chunks_retrieved: Número de chunks recuperados
            avg_similarity: Similaridade média dos chunks
            response_time_ms: Tempo de resposta em ms
            tokens_used: Tokens usados na geração
            trail_id: Trilha do founder
            step_id: Etapa do founder
            user_id: ID do usuário
            sources: Lista de documentos fonte usados
        """
        import uuid
        
        had_context = chunks_retrieved > 0
        sources = sources or []
        
        # Cria métrica individual
        metric = QueryMetric(
            query_id=str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow().isoformat(),
            question=question[:200],  # Trunca para não explodir
            trail_id=trail_id,
            step_id=step_id,
            user_id=user_id,
            chunks_retrieved=chunks_retrieved,
            avg_similarity=avg_similarity,
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
            had_context=had_context,
            sources_used=sources[:5]  # Limita a 5 fontes
        )
        
        # Loga query
        self._log_query(metric)
        
        # Atualiza métricas agregadas
        with _metrics_lock:
            m = self.metrics
            m["total_queries"] = m.get("total_queries", 0) + 1
            
            if had_context:
                m["queries_with_context"] = m.get("queries_with_context", 0) + 1
            else:
                m["queries_without_context"] = m.get("queries_without_context", 0) + 1
            
            m["total_response_time_ms"] = m.get("total_response_time_ms", 0) + response_time_ms
            m["total_chunks_retrieved"] = m.get("total_chunks_retrieved", 0) + chunks_retrieved
            m["total_similarity_score"] = m.get("total_similarity_score", 0.0) + avg_similarity
            m["total_tokens_used"] = m.get("total_tokens_used", 0) + tokens_used
            
            # Por trilha
            if trail_id:
                if "queries_by_trail" not in m:
                    m["queries_by_trail"] = {}
                m["queries_by_trail"][trail_id] = m["queries_by_trail"].get(trail_id, 0) + 1
            
            # Por dia
            today = datetime.utcnow().strftime("%Y-%m-%d")
            if "queries_by_day" not in m:
                m["queries_by_day"] = {}
            m["queries_by_day"][today] = m["queries_by_day"].get(today, 0) + 1
            
            # Contagem de queries similares
            q_key = question[:50].lower()
            if "query_counts" not in m:
                m["query_counts"] = {}
            m["query_counts"][q_key] = m["query_counts"].get(q_key, 0) + 1
            
            # Uso de documentos
            if "doc_usage" not in m:
                m["doc_usage"] = {}
            for src in sources:
                m["doc_usage"][src] = m["doc_usage"].get(src, 0) + 1
        
        # Salva periodicamente (a cada 10 queries)
        if self.metrics.get("total_queries", 0) % 10 == 0:
            self._save_metrics()
    
    # ======================================================
    # Consulta de Métricas
    # ======================================================
    
    def get_summary(self) -> RAGMetrics:
        """Retorna resumo das métricas"""
        m = self.metrics
        total = m.get("total_queries", 0) or 1  # Evita divisão por zero
        
        # Calcula queries por período
        today = datetime.utcnow().strftime("%Y-%m-%d")
        week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        month_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        queries_by_day = m.get("queries_by_day", {})
        
        queries_today = queries_by_day.get(today, 0)
        queries_week = sum(
            v for k, v in queries_by_day.items() 
            if k >= week_ago
        )
        queries_month = sum(
            v for k, v in queries_by_day.items() 
            if k >= month_ago
        )
        
        # Top queries
        query_counts = m.get("query_counts", {})
        top_queries = sorted(
            [{"query": k, "count": v} for k, v in query_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        # Top documentos
        doc_usage = m.get("doc_usage", {})
        top_docs = sorted(
            [{"document": k, "usage_count": v} for k, v in doc_usage.items()],
            key=lambda x: x["usage_count"],
            reverse=True
        )[:10]
        
        return RAGMetrics(
            total_queries=m.get("total_queries", 0),
            queries_with_context=m.get("queries_with_context", 0),
            queries_without_context=m.get("queries_without_context", 0),
            avg_response_time_ms=m.get("total_response_time_ms", 0) / total,
            avg_chunks_retrieved=m.get("total_chunks_retrieved", 0) / total,
            avg_similarity_score=m.get("total_similarity_score", 0.0) / total,
            total_tokens_used=m.get("total_tokens_used", 0),
            queries_today=queries_today,
            queries_this_week=queries_week,
            queries_this_month=queries_month,
            queries_by_trail=m.get("queries_by_trail", {}),
            top_queries=top_queries,
            top_documents=top_docs
        )
    
    def get_queries_history(self, limit: int = 100) -> List[Dict]:
        """Retorna histórico de queries recentes"""
        queries = []
        
        if not os.path.exists(QUERIES_LOG_FILE):
            return queries
        
        try:
            with open(QUERIES_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()[-limit:]  # Últimas N linhas
                for line in reversed(lines):
                    try:
                        queries.append(json.loads(line.strip()))
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ Erro ao ler histórico: {e}")
        
        return queries
    
    def get_daily_stats(self, days: int = 30) -> List[Dict]:
        """Retorna estatísticas diárias"""
        stats = []
        queries_by_day = self.metrics.get("queries_by_day", {})
        
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            stats.append({
                "date": date,
                "queries": queries_by_day.get(date, 0)
            })
        
        return list(reversed(stats))
    
    def reset_metrics(self):
        """Reseta todas as métricas (use com cuidado!)"""
        with _metrics_lock:
            self.metrics = {
                "total_queries": 0,
                "queries_with_context": 0,
                "queries_without_context": 0,
                "total_response_time_ms": 0,
                "total_chunks_retrieved": 0,
                "total_similarity_score": 0.0,
                "total_tokens_used": 0,
                "queries_by_trail": {},
                "queries_by_day": {},
                "query_counts": {},
                "doc_usage": {},
                "last_updated": datetime.utcnow().isoformat()
            }
            self._save_metrics()


# Instância global
rag_metrics = RAGMetricsService()


# ======================================================
# Funções de Conveniência
# ======================================================

def record_rag_query(
    question: str,
    chunks_retrieved: int,
    avg_similarity: float,
    response_time_ms: int,
    **kwargs
):
    """Função de conveniência para registrar query"""
    rag_metrics.record_query(
        question=question,
        chunks_retrieved=chunks_retrieved,
        avg_similarity=avg_similarity,
        response_time_ms=response_time_ms,
        **kwargs
    )


def get_rag_metrics() -> Dict[str, Any]:
    """Retorna métricas como dicionário"""
    summary = rag_metrics.get_summary()
    return asdict(summary)


def get_rag_history(limit: int = 100) -> List[Dict]:
    """Retorna histórico de queries"""
    return rag_metrics.get_queries_history(limit)


def get_daily_stats(days: int = 30) -> List[Dict]:
    """Retorna stats diárias"""
    return rag_metrics.get_daily_stats(days)
