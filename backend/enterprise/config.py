"""
Enterprise Configuration & Feature Flags
=========================================

Sistema central de controle para todos os subsistemas enterprise.
Nada é executado sem estar aqui habilitado.

IMPORTANTE:
- Por padrão, TODOS os features estão DESLIGADOS (False)
- Podem ser ativados via:
  1. Variáveis de ambiente
  2. Arquivo .env.enterprise
  3. Runtime flags (debug apenas)

Exemplo .env.enterprise:
  ENTERPRISE_DECISION_LEDGER=true
  ENTERPRISE_METHOD_GOVERNANCE=true
  ENTERPRISE_RISK_ENGINE=false
"""

import os
from dataclasses import dataclass
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class EnterpriseFeatureFlags:
    """Container imutável de feature flags."""
    
    decision_ledger: bool = False
    method_governance: bool = False
    risk_engine: bool = False
    template_engine: bool = False
    cognitive_memory: bool = False
    ai_audit: bool = False
    cognitive_signals: bool = False
    verticalization: bool = False
    
    def to_dict(self) -> Dict[str, bool]:
        """Converte para dict para logging."""
        return {
            "decision_ledger": self.decision_ledger,
            "method_governance": self.method_governance,
            "risk_engine": self.risk_engine,
            "template_engine": self.template_engine,
            "cognitive_memory": self.cognitive_memory,
            "ai_audit": self.ai_audit,
            "cognitive_signals": self.cognitive_signals,
            "verticalization": self.verticalization,
        }
    
    def is_any_enabled(self) -> bool:
        """Retorna True se algum feature está ativo."""
        return any(self.to_dict().values())


def get_enterprise_config() -> EnterpriseFeatureFlags:
    """
    Carrega configuração enterprise a partir de variáveis de ambiente.
    
    Checklist:
    1. Lê .env.enterprise se existir
    2. Faz override com variáveis de ambiente
    3. Valida compatibilidade
    4. Loga estado
    
    Returns:
        EnterpriseFeatureFlags com estado atual
    """
    
    # 1. Valores padrão (tudo desligado)
    flags_dict = {
        "decision_ledger": False,
        "method_governance": False,
        "risk_engine": False,
        "template_engine": False,
        "cognitive_memory": False,
        "ai_audit": False,
        "cognitive_signals": False,
        "verticalization": False,
    }
    
    # 2. Lê arquivo .env.enterprise se existir
    env_file = os.path.join(os.path.dirname(__file__), ".env.enterprise")
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip().lower()
                            value = value.strip().lower()
                            
                            # Mapeia ENTERPRISE_FEATURE_NAME → feature_name
                            if key.startswith('enterprise_'):
                                feature_key = key.replace('enterprise_', '')
                                if feature_key in flags_dict:
                                    flags_dict[feature_key] = value in ('true', '1', 'yes', 'on')
            logger.info(f"✓ Carregado .env.enterprise")
        except Exception as e:
            logger.warning(f"⚠ Erro ao ler .env.enterprise: {e}")
    
    # 3. Override com variáveis de ambiente
    env_overrides = {
        "ENTERPRISE_DECISION_LEDGER": "decision_ledger",
        "ENTERPRISE_METHOD_GOVERNANCE": "method_governance",
        "ENTERPRISE_RISK_ENGINE": "risk_engine",
        "ENTERPRISE_TEMPLATE_ENGINE": "template_engine",
        "ENTERPRISE_COGNITIVE_MEMORY": "cognitive_memory",
        "ENTERPRISE_AI_AUDIT": "ai_audit",
        "ENTERPRISE_COGNITIVE_SIGNALS": "cognitive_signals",
        "ENTERPRISE_VERTICALIZATION": "verticalization",
    }
    
    for env_key, feature_key in env_overrides.items():
        env_value = os.getenv(env_key, "").lower()
        if env_value in ('true', '1', 'yes', 'on'):
            flags_dict[feature_key] = True
            logger.info(f"✓ Feature '{feature_key}' ativado via {env_key}")
    
    # 4. Cria objeto
    config = EnterpriseFeatureFlags(**flags_dict)
    
    # 5. Log do estado
    if config.is_any_enabled():
        logger.info(f"🏛️  ENTERPRISE MODE ATIVADO - Features: {config.to_dict()}")
    else:
        logger.debug("ℹ️  Modo Enterprise desligado (todos features False)")
    
    return config


# Singleton
_enterprise_config = None


def get_or_create_enterprise_config() -> EnterpriseFeatureFlags:
    """Retorna singleton da configuração enterprise."""
    global _enterprise_config
    if _enterprise_config is None:
        _enterprise_config = get_enterprise_config()
    return _enterprise_config
