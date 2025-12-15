"use client";

import { useState } from "react";
import axios from "axios";

export default function FounderChat() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const backendBase = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  async function handleSend(e) {
    e?.preventDefault();
    if (!input.trim()) return;

    const question = input.trim();
    setInput("");
    setHistory((prev) => [...prev, { role: "founder", text: question }]);
    setLoading(true);

    try {
      console.log("Enviando para:", `${backendBase}/chat/`);
      const res = await axios.post(`${backendBase}/chat/`, { question });
      console.log("Resposta completa:", res.data);
      
      // Extrai o answer corretamente: res.data = {status: "success", data: {answer: "texto"}}
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
    } catch (err) {
      console.error("Erro ao chamar backend:", err);
      const errorMsg = err.response?.data?.detail || err.message || "Erro desconhecido";
      
      setHistory((prev) => [
        ...prev,
        {
          role: "agent",
          text: `❌ Erro: ${errorMsg}\n\nBackend: ${backendBase}/chat/`
        }
      ]);
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
