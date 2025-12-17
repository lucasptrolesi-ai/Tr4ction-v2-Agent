"use client";

import { useState } from "react";
import axios from "axios";

export default function FounderChat() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const backendBase = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const MAX_RETRIES = 2;

  async function handleSend(e, retryAttempt = 0) {
    e?.preventDefault();
    if (!input.trim()) return;

    const question = input.trim();
    if (retryAttempt === 0) {
      setInput("");
      setHistory((prev) => [...prev, { role: "founder", text: question }]);
    }
    setLoading(true);

    try {
      console.log(`[Tentativa ${retryAttempt + 1}] Enviando para: ${backendBase}/chat/`);
      const res = await axios.post(
        `${backendBase}/chat/`,
        { question },
        { timeout: 30000 } // 30 segundos de timeout
      );
      console.log("Resposta completa:", res.data);
      
      // Extrai o answer corretamente
      let answer = "";
      if (res.data?.data?.answer) {
        answer = res.data.data.answer;
      } else if (res.data?.answer) {
        answer = res.data.answer;
      } else if (typeof res.data === "string") {
        answer = res.data;
      } else {
        answer = JSON.stringify(res.data);
      }

      setHistory((prev) => [...prev, { role: "agent", text: answer }]);
      setRetryCount(0);
    } catch (err) {
      console.error("Erro ao chamar backend:", err);
      
      const isNetworkError = err.code === "ECONNABORTED" || err.code === "ENOTFOUND" || 
                           (err.response?.status >= 500);
      const shouldRetry = isNetworkError && retryAttempt < MAX_RETRIES;
      
      if (shouldRetry) {
        console.log(`Retentando em 2s... (${retryAttempt + 1}/${MAX_RETRIES})`);
        setRetryCount(retryAttempt + 1);
        setTimeout(() => {
          handleSend(e, retryAttempt + 1);
        }, 2000);
        return;
      }

      const errorMsg = err.response?.data?.detail || 
                      err.message || 
                      "Erro ao comunicar com o servidor";
      
      const retryInfo = shouldRetry ? "" : 
        ` (Tentativas: ${retryAttempt}/${MAX_RETRIES})`;
      
      setHistory((prev) => [
        ...prev,
        {
          role: "agent",
          text: `❌ Erro: ${errorMsg}${retryInfo}\n\nDica: Verifique sua conexão e tente novamente.`
        }
      ]);
      setRetryCount(0);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>Chat com o TR4CTION Agent</h1>
      <p style={{ color: "var(--text-muted)", maxWidth: 620 }}>
        Peça ajuda para preencher ICP, Persona, SWOT, JTBD ou tirar dúvidas sobre
        os materiais do programa.
      </p>

      <div
        style={{
          marginTop: 20,
          borderRadius: 18,
          border: "1px solid var(--border)",
          background: "#fff",
          padding: 16,
          minHeight: 280,
          maxHeight: 420,
          overflowY: "auto"
        }}
      >
        {history.length === 0 && (
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Ex.: "Explique o que é ICP para uma startup B2B SaaS" ou
            "Me ajude a esboçar a Persona da minha solução".
          </p>
        )}

        {history.map((m, i) => (
          <div
            key={i}
            style={{
              marginBottom: 10,
              textAlign: m.role === "founder" ? "right" : "left"
            }}
          >
            <div
              style={{
                display: "inline-block",
                padding: "8px 12px",
                borderRadius: 12,
                background:
                  m.role === "founder" ? "var(--primary)" : "var(--primary-soft)",
                color: m.role === "founder" ? "#fff" : "var(--deep)",
                fontSize: "0.9rem"
              }}
            >
              {m.text}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            O agente está pensando...
          </div>
        )}
      </div>

      <form
        onSubmit={handleSend}
        style={{ marginTop: 16, display: "flex", gap: 8 }}
      >
        <input
          className="input"
          placeholder="Digite sua pergunta para o agente..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="btn btn-primary" type="submit" disabled={loading}>
          Enviar
        </button>
      </form>
    </div>
  );
}
