/**
 * ✅ AJUSTE 5: Endurecimento do Frontend - Trilhas Educacionais
 * 
 * GARANTIAS:
 * - Frontend NUNCA calcula próxima pergunta localmente
 * - Backend é autoridade absoluta de sequência
 * - Em refresh, estado é recuperado do backend
 * - Sem lógica de ordem no cliente
 * - Backend retorna próxima pergunta válida
 */

'use client';

import React, { useState, useEffect } from 'react';

interface Question {
  field_id: string;
  label: string;
  inferred_type: string;
  required: boolean;
  order_index: number;
}

interface TrailProgress {
  progress_percent: number;
  answered: number;
  total: number;
  next_question: Question | null;
  is_complete: boolean;
}

interface TemplateTrailProps {
  templateId: string;
  founderId: string;
}

/**
 * ✅ AJUSTE 5: Componente de trilha sem lógica de ordem
 * 
 * Responsabilidades do componente:
 * ❌ NÃO: Calcular próxima pergunta
 * ❌ NÃO: Manter índice de pergunta
 * ❌ NÃO: Permitir navegação arbitrária
 * ✅ SIM: Exibir pergunta do backend
 * ✅ SIM: Enviar resposta ao backend
 * ✅ SIM: Recuperar próximo do backend
 * ✅ SIM: Listar todas as perguntas (status apenas)
 */
export function TemplateTrail({ templateId, founderId }: TemplateTrailProps) {
  // Estado
  const [allQuestions, setAllQuestions] = useState<Question[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [progress, setProgress] = useState<TrailProgress | null>(null);
  const [answeredFields, setAnsweredFields] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  /**
   * ✅ AJUSTE 5: Recuperar estado completo do backend
   * 
   * Em mount ou refresh:
   * 1. GET /trails/{templateId}/trail → todas as perguntas (lista)
   * 2. GET /trails/{templateId}/progress → próxima pergunta + progresso
   */
  useEffect(() => {
    const loadTrailState = async () => {
      try {
        setLoading(true);
        setError(null);

        // 1. Carregar lista de perguntas (para exibir sidebar)
        const trailRes = await fetch(
          `/api/v1/trails/templates/${templateId}/trail`
        );
        if (!trailRes.ok) {
          throw new Error('Falha ao carregar trilha');
        }
        const trailData = await trailRes.json();
        setAllQuestions(trailData.questions);

        // 2. ✅ Carregar próxima pergunta do BACKEND (não calcular no frontend)
        const progressRes = await fetch(
          `/api/v1/trails/templates/${templateId}/progress?founder_id=${founderId}`
        );
        if (!progressRes.ok) {
          throw new Error('Falha ao carregar progresso');
        }
        const progressData = await progressRes.json() as TrailProgress;
        setProgress(progressData);
        setCurrentQuestion(progressData.next_question);

        // 3. Atualizar lista de respostas
        const answered = new Set<string>();
        if (progressData.answered > 0) {
          // ✅ Derivar respostas a partir do progresso
          for (const q of trailData.questions) {
            if (q.order_index < progressData.answered) {
              answered.add(q.field_id);
            }
          }
        }
        setAnsweredFields(answered);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erro desconhecido';
        setError(message);
        console.error('❌ Erro ao carregar trilha:', message);
      } finally {
        setLoading(false);
      }
    };

    loadTrailState();
  }, [templateId, founderId]);

  /**
   * ✅ AJUSTE 5: Enviar resposta com backend como autoridade
   * 
   * POST /answer:
   * 1. Enviar resposta
   * 2. Backend valida sequência
   * 3. Se OK, backend retorna próxima pergunta
   * 4. Se erro, frontend exibe mensagem
   */
  const handleSubmitAnswer = async (answer: string) => {
    if (!currentQuestion) return;

    try {
      setSubmitting(true);
      setError(null);

      const response = await fetch(
        `/api/v1/trails/templates/${templateId}/answer/${currentQuestion.field_id}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answer }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || 'Falha ao salvar resposta'
        );
      }

      // Sucesso - atualizar estado
      const result = await response.json();

      // Atualizar lista de respostas
      setAnsweredFields((prev) => {
        const updated = new Set(prev);
        updated.add(currentQuestion.field_id);
        return updated;
      });

      // ✅ Próxima pergunta vem do backend, não calculamos aqui
      setCurrentQuestion(result.next_question);

      // Recarregar progresso
      const progressRes = await fetch(
        `/api/v1/trails/templates/${templateId}/progress?founder_id=${founderId}`
      );
      if (progressRes.ok) {
        const progressData = await progressRes.json();
        setProgress(progressData);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(message);
      console.error('❌ Erro ao salvar resposta:', message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="trail-container">
        <div className="loading">Carregando trilha educacional...</div>
      </div>
    );
  }

  return (
    <div className="trail-container">
      {/* Barra de progresso */}
      {progress && (
        <div className="progress-section">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress.progress_percent}%` }}
            >
              {progress.progress_percent}%
            </div>
          </div>
          <div className="progress-text">
            {progress.answered} de {progress.total} respondidas
          </div>
        </div>
      )}

      {/* Pergunta atual */}
      <div className="question-section">
        {currentQuestion ? (
          <QuestionCard
            question={currentQuestion}
            onSubmit={handleSubmitAnswer}
            disabled={submitting}
            isLoading={submitting}
          />
        ) : (
          <div className="completion-message">
            ✅ Trilha completa! Você respondeu todas as perguntas.
          </div>
        )}

        {error && (
          <div className="error-message">
            ❌ {error}
          </div>
        )}
      </div>

      {/* Lista de perguntas com status */}
      <div className="questions-list">
        <h3>Perguntas da Trilha</h3>
        <ul>
          {allQuestions.map((q, idx) => {
            const isAnswered = answeredFields.has(q.field_id);
            const isCurrent = currentQuestion?.field_id === q.field_id;

            return (
              <li
                key={q.field_id}
                className={`question-item ${isAnswered ? 'answered' : 'pending'} ${
                  isCurrent ? 'current' : ''
                }`}
              >
                <span className="order">{idx + 1}.</span>
                <span className="text">{q.label || `Pergunta ${idx + 1}`}</span>
                <span className="status">
                  {isAnswered ? '✅' : isCurrent ? '▶️' : '⏳'}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

interface QuestionCardProps {
  question: Question;
  onSubmit: (answer: string) => Promise<void>;
  disabled?: boolean;
  isLoading?: boolean;
}

/**
 * ✅ AJUSTE 5: Componente de pergunta
 * 
 * Simples:
 * - Exibe pergunta do backend
 * - Campo de entrada
 * - Botão enviar (com loading state)
 * - Sem lógica de navegação
 */
function QuestionCard({
  question,
  onSubmit,
  disabled,
  isLoading,
}: QuestionCardProps) {
  const [answer, setAnswer] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim()) return;
    await onSubmit(answer);
    setAnswer('');
  };

  return (
    <div className="question-card">
      <h2>{question.label}</h2>
      <div className="question-metadata">
        <span className="field-id">ID: {question.field_id}</span>
        <span className="field-type">{question.inferred_type}</span>
        {question.required && <span className="required">Obrigatório</span>}
      </div>

      <form onSubmit={handleSubmit}>
        <textarea
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Digite sua resposta..."
          disabled={disabled || isLoading}
          required={question.required}
          rows={4}
        />

        <button
          type="submit"
          disabled={!answer.trim() || disabled || isLoading}
        >
          {isLoading ? 'Salvando...' : 'Enviar Resposta'}
        </button>
      </form>
    </div>
  );
}

/* Estilos básicos */
const styles = `
.trail-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

.progress-section {
  margin-bottom: 30px;
}

.progress-bar {
  background: #e0e0e0;
  height: 30px;
  border-radius: 15px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  background: linear-gradient(90deg, #4CAF50, #45a049);
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  transition: width 0.3s ease;
}

.progress-text {
  text-align: right;
  font-size: 14px;
  color: #666;
}

.question-section {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
}

.question-card {
  margin-bottom: 20px;
}

.question-card h2 {
  margin: 0 0 15px 0;
  font-size: 24px;
  color: #333;
}

.question-metadata {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  font-size: 12px;
  color: #999;
}

.required {
  color: #f44336;
  font-weight: bold;
}

.question-card form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.question-card textarea {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
}

.question-card button {
  padding: 10px 20px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
}

.question-card button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.completion-message {
  text-align: center;
  padding: 40px;
  font-size: 18px;
  color: #4CAF50;
  background: #f1f8f6;
  border-radius: 8px;
}

.error-message {
  margin-top: 15px;
  padding: 12px;
  background: #ffebee;
  color: #c62828;
  border-left: 4px solid #c62828;
  border-radius: 4px;
}

.questions-list {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
}

.questions-list h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #333;
}

.questions-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.question-item {
  padding: 10px;
  margin-bottom: 5px;
  border-left: 4px solid #ddd;
  display: flex;
  align-items: center;
  gap: 10px;
  border-radius: 4px;
  transition: background 0.2s;
}

.question-item.answered {
  border-left-color: #4CAF50;
  background: #f1f8f6;
}

.question-item.pending {
  border-left-color: #ff9800;
  background: #fff8f0;
}

.question-item.current {
  border-left-color: #2196F3;
  background: #f0f7ff;
  font-weight: bold;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 16px;
}
`;

export const trailStyles = styles;
