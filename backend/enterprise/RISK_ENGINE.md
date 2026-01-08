# Risk Engine (Phase 2)

## Objetivo
Detectar incoerência estratégica real e registrar evidências explicáveis. Observação por padrão; bloqueio opcional via `ENABLE_RISK_BLOCKING`.

## Entidades
- **RiskAssessment** (runtime): `overall_risk`, `red_flags[]`, `trust_score`, `coherence_score`, `decision_maturity`.
- **RedFlag**: `flag_type` (generic_response, coherence_violation, frequent_changes, data_quality, assumption_gap, market_mismatch), `severity`, `evidence`, `violated_dependencies`, `recommendation`.
- **RiskSignal** (DB): `client_id`, `template_key`, `risk_type`, `severity`, `evidence`, `violated_dependencies`, `recommendation`, `related_decisions`, `created_at`.

## Checks mínimas
- Respostas genéricas e curtas.
- ICP ↔ Persona (coerência simples).
- Mudanças frequentes vs histórico.
- Premissas ativas não refletidas (assumption_gap).
- Mismatch B2B/B2C (heurística em constraints).

## Fluxo (save template)
1) Avalia risco com `RiskDetectionEngine.assess_template_response` (premissas incluídas).
2) Persiste `RiskSignal` (append-only) e `risk_result` no Decision Ledger.
3) Loga no AI Audit se `ai_audit` ligado.
4) Bloqueio somente se `ENABLE_RISK_BLOCKING=true` e risco HIGH/CRITICAL.

## Feature Flags
- `ENTERPRISE_RISK_ENGINE` → habilita avaliação (observação).
- `ENABLE_RISK_BLOCKING` → permite bloqueio em HIGH/CRITICAL.

## Saída para Front (opcional)
`cognitive_signals` retornados no save:
- `risk_level`
- `strategic_alert`
- `violated_dependencies`
- `learning_feedback`

## Critérios
- Flags off → zero bloqueio; contratos preservados.
- Dados append-only; decisões antigas intactas.
