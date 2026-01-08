# AI Governance Model - Phase 1 (Observation Only)

## Objetivo
Garantir rastreabilidade e explicabilidade de todas as respostas de IA sem bloquear fluxo existente.

## Componentes
- **AIAuditLog**: append-only, registra prompt hash/versão, modelo/versão, contexto (incl. premissas), regras ativas.
- **Feature Flags**: `ai_audit`, `enable_premises_enforcement`, `enable_governance_gates`, `enable_risk_blocking` (todos desligados por padrão).
- **Client Premises**: premissas versionadas e obrigatoriamente associadas ao contexto de IA (fallback seguro se ausentes).

## Regras (Fase 1)
- Nenhuma resposta é bloqueada.
- Se premissas ativas não existirem, contexto usa fallback e gera aviso de auditoria (quando `ai_audit` ligado).
- Logs são somente leitura; sem dados sensíveis (IDs e hashes apenas).

## Campos AIAuditLog
- `response_id`, `event_type`, `model`, `model_version`
- `prompt_hash`, `prompt_version`, `system_prompt_hash`, `system_prompt_version`
- `context_snapshot` (inclui premissas), `validation_rules_applied`, `governance_rules_active`
- `tokens_used`, `latency_ms`, `success`, `error_message`

## Operação
1. Flags ficam **off** por padrão.
2. Ative `ENTERPRISE_AI_AUDIT=true` para registrar eventos.
3. Exporte consultas via rota `/enterprise/ai-audit/trail/{startup_id}` (admin only).

## Próximos Passos (Futuro)
- Bloqueio configurável em riscos críticos (`enable_risk_blocking`).
- Gating metodológico (`enable_governance_gates`).
- Export formal (CSV/NDJSON) para compliance.
