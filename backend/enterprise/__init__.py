"""
TR4CTION Enterprise Module
==========================

Subsistemas de nivel institucional para transformar TR4CTION em produto FCJ.

REGRA OURO:
- Tudo é opcional (feature flags)
- Tudo está desligado por padrão
- Zero impacto no sistema existente
- 100% retrocompatível

Subsistemas:
1. Decision Ledger       - Rastreabilidade de decisões
2. Method Governance    - Enforcement de regras FCJ
3. AI Risk Detection    - Classificação de risco
4. Cognitive Memory     - Persistência de contexto
5. Template Engine      - Orquestração dinâmica
6. AI Audit             - Compliance de IA
7. Cognitive Signals    - Sinais para Frontend
8. Verticalization      - Suporte a múltiplas verticais
"""

from .config import get_enterprise_config, EnterpriseFeatureFlags

__all__ = ["get_enterprise_config", "EnterpriseFeatureFlags"]
