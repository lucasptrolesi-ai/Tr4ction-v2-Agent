# Governance Engine (Phase 2)

## Objetivo
Codificar o método FCJ como regras institucionais, versionadas e auditáveis. Observação por padrão; bloqueio apenas quando `ENABLE_GOVERNANCE_GATES=true`.

## Entidades
- **GovernanceGate** (DB):
  - `id`, `template_id`, `vertical`, `required_fields[]`, `validation_rules[]`, `min_completeness_score`, `block_on_fail`, `version`, `created_at`
  - Append-only; selecionar sempre a última versão por template/vertical.
- **GovernanceGateResult** (runtime):
  - `passed`, `violations[]`, `gate_version`, `completeness_score`, `block_on_fail`.

## Fluxo (save template)
1) Carrega premissas (ativa ou fallback).
2) Carrega gate mais recente (`GovernanceGateService.latest_gate`).
3) Avalia com `GovernanceEngine.evaluate_gate`.
4) Registra resultado no Decision Ledger (`governance_result`).
5) Registra no AI Audit (se `ai_audit` ligado).
6) Bloqueia somente se `ENABLE_GOVERNANCE_GATES=true` **e** `block_on_fail=true`.

## Feature Flags
- `ENTERPRISE_METHOD_GOVERNANCE` → habilita avaliação (observação).
- `ENABLE_GOVERNANCE_GATES` → permite bloqueio quando gate falha.

## APIs
- `POST /enterprise/governance/validate` (existente): segue observacional.
- Save de templates agora executa gates automaticamente (observação por default).

## Dados e Versões
- Gates são dados em tabela `governance_gates` (append-only).
- Versão usada em cada decisão é armazenada no `governance_result` do ledger.

## Critérios
- Sem feature flag → nenhum bloqueio, apenas cálculo quando ativado.
- Campos novos são opcionais; contratos existentes mantidos.
