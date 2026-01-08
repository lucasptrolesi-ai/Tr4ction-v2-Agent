# Decision Intelligence Ledger - Spec (Phase 1)

## Objetivo
Rastrear decisões de founders como ativos auditáveis, sem bloquear fluxo.

## Modelo `decision_events`
- `id` (uuid, pk)
- `user_id`, `user_email`, `startup_id`
- `template_key`, `field_key`, `field_label`, `step_id`
- `previous_value`, `new_value`, `value_type`
- `fcj_method_version`, `method_version`, `cycle`, `vertical`
- `premises_used[]`, `ai_recommendation`, `risk_level`, `human_confirmation`
- `related_template_snapshot`
- `expected_outcome`, `actual_outcome`, `outcome_success`, `outcome_verified_at`
- `created_at`

## Regras
- Append-only (novo registro a cada mudança relevante).
- Alterações geram nova versão; registros antigos nunca são sobrescritos.
- Compatível com eventos antigos (campos novos são opcionais).

## API (read-only)
- `GET /enterprise/decisions/history/{startup_id}`
  - Filtros: `template_key`, `risk_level`, `method_version`, `vertical`, `limit`
- `GET /enterprise/decisions/{startup_id}/{template_key}/{field_key}`
- `GET /enterprise/decisions/audit/summary/{startup_id}`

## Integração
- `record_decision(...)` aceita `premises_used`, `ai_recommendation`, `risk_level`, `human_confirmation`, `method_version`, `vertical`.
- Campos novos são opcionais; value_type calculado automaticamente.

## Feature Flags
- `ENTERPRISE_DECISION_LEDGER` controla criação/consulta.
- Observabilidade apenas; nenhum bloqueio.

## Migração
Use `scripts/migrations/20260108_phase1_enterprise.py` para adicionar colunas e criar tabela.
