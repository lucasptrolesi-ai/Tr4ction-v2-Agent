# Cognitive UX Model (Phase 3) - VALIDADO

## Payload Padrão (Defensive Design)

```json
{
  "cognitive_signals": {
    "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
    "strategic_alert": "frase curta e executiva",
    "blocking_reason": "explicação informativa (null se flag OFF)",
    "violated_dependencies": ["ICP → Persona", "Canal → Persona"],
    "learning_feedback": "orientação didática e objetiva"
  }
}
```

## Características Validadas

### 1. Observabilidade Pura
- **Risco é informativo**: sem bloqueio automático
- `blocking_reason` apenas informativo (nunca força bloqueio)
- Sistema funciona sem sinais (campos opcionais)

### 2. Linguagem Executiva
- Frases diretas, sem jargão técnico
- Max 140–180 caracteres por campo
- Tom neutro e orientativo
- Prefere: "Revisar entrega" vs "Riscos acima do aceitável"

### 3. Defensive Design
- Null-safety total em formatter
- Type validation em todos níveis
- Fallbacks seguros
- Nenhuma exception por payload parcial

### 4. Fontes de Dados
- `risk_level`: derivado de `RiskDetectionEngine.overall_risk`
- `strategic_alert`: primeira red flag ou recommendation
- `violated_dependencies`: extração de red flags (dedupe)
- `learning_feedback`: suggestions dos flags ou recommendations
- `blocking_reason`: só aparece se `enable_risk_blocking=True`

### 5. Consistência Cognitiva
- LOW → nenhum alerta (sinal verde)
- MEDIUM → alerta leve, informativo
- HIGH → alerta estratégico claro
- CRITICAL → mesmo comportamento (sem bloqueio a menos que flag ativa)

## Diretrizes de Redação (Validadas)

### ✅ Prefira:
- "Resposta precisa de mais detalhes"
- "ICP e Persona não estão alinhados"
- "Considere validar sua estratégia"
- "Alinhe ICP ao modelo B2B declarado"

### ❌ Evite:
- "Resposta muito genérica (score: 3.2)"
- "Founder mudou respostas múltiplas vezes"
- "Isso sugere indecisão"
- Linguagem acusatória ou julgadora

## Uso no Frontend

### Componentes (Mobile-First)
- `RiskBadge`: cor + nível, null-safe
- `StrategicAlert`: card com ícone, valida tipo
- `DependencyHint`: lista vertical, filtra inválidos
- `LearningTooltip`: expansível em toque, aria-labels

### Renderização Condicional
```jsx
{cognitiveSignals && (
  <>
    <RiskBadge level={cognitiveSignals.risk_level} />
    <StrategicAlert text={cognitiveSignals.strategic_alert} />
    <DependencyHint items={cognitiveSignals.violated_dependencies} />
    <LearningTooltip text={cognitiveSignals.learning_feedback} />
  </>
)}
```

### Fail-Safe
- Se `cognitiveSignals` for `null/undefined`, nada quebra
- Cada componente valida props internamente
- Frontend idêntico com ou sem sinais

## Aceite Enterprise

- ✅ Compatibilidade total com frontend atual
- ✅ Nenhum campo obrigatório adicionado
- ✅ Defensive design validado
- ✅ Linguagem executiva aplicada
- ✅ Mobile-friendly confirmado
- ✅ Pronto para auditoria e conselho
