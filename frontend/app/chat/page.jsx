"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import axios from "axios";

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState([
    {
      role: "agent",
      text: "Olá! 👋 Sou o Assistente TR4CTION. Estou aqui para ajudar você a preencher os templates do programa.\n\nPosso ajudar com:\n• **ICP + Persona** - Identificar seu cliente ideal\n• **SWOT** - Análise de mercado\n• **Go-to-Market** - Estratégia de lançamento\n• **Pitch Deck** - Para investidores\n• **Roadmap** - Planejamento do produto\n• **Landing Page** - Copy e estrutura\n\nComo posso ajudar você?"
    }
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const backendBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [history]);

  const handleSend = useCallback(async (e) => {
    if (e) {
      e.preventDefault();
    }
    
    const trimmedInput = input.trim();
    if (!trimmedInput) return;

    setInput("");
    setHistory((prev) => [...prev, { role: "user", text: trimmedInput }]);
    setLoading(true);

    try {
      console.log(`Enviando para: ${backendBase}/chat/`);
      const response = await axios.post(
        `${backendBase}/chat/`,
        { question: trimmedInput },
        { timeout: 30000 }
      );

      let answer = "";
      if (response?.data?.data?.answer) {
        answer = response.data.data.answer;
      } else if (response?.data?.answer) {
        answer = response.data.answer;
      } else if (typeof response?.data === "string") {
        answer = response.data;
      } else {
        answer = JSON.stringify(response?.data || "Sem resposta");
      }

      setHistory((prev) => [...prev, { role: "agent", text: answer }]);
    } catch (error) {
      console.error("Erro:", error);
      const errorMessage = error?.response?.data?.detail || error?.message || "Erro ao comunicar com servidor";
      setHistory((prev) => [...prev, { role: "agent", text: `❌ Desculpe, ocorreu um erro: ${errorMessage}\n\nDica: Certifique-se de que o backend está rodando em ${backendBase}` }]);
    } finally {
      setLoading(false);
    }
  }, [input, backendBase]);

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      background: "#ffffff"
    }}>
      {/* HEADER */}
      <div style={{
        padding: "20px 30px",
        borderBottom: "1px solid #e0e0e0",
        background: "#f9f9f9"
      }}>
        <h1 style={{ margin: 0, fontSize: "28px", fontWeight: "600", color: "#1a1a1a" }}>
          🚀 TR4CTION Agent
        </h1>
        <p style={{ margin: "5px 0 0 0", color: "#666", fontSize: "14px" }}>
          Assistente para preencher templates e estratégias
        </p>
      </div>

      {/* CHAT MESSAGES */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "30px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        maxWidth: "900px",
        margin: "0 auto",
        width: "100%"
      }}>
        {history.map((msg, idx) => (
          <div
            key={idx}
            style={{
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              gap: "12px"
            }}
          >
            {msg.role === "agent" && (
              <div style={{
                fontSize: "28px",
                flexShrink: 0,
                width: "40px",
                height: "40px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}>
                🤖
              </div>
            )}
            
            <div style={{
              maxWidth: "65%",
              padding: "12px 16px",
              borderRadius: "16px",
              background: msg.role === "user" ? "#007bff" : "#f0f0f0",
              color: msg.role === "user" ? "white" : "#1a1a1a",
              lineHeight: "1.5",
              whiteSpace: "pre-wrap",
              wordWrap: "break-word"
            }}>
              {msg.text}
            </div>

            {msg.role === "user" && (
              <div style={{
                fontSize: "28px",
                flexShrink: 0,
                width: "40px",
                height: "40px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}>
                👤
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{
            display: "flex",
            gap: "12px",
            alignItems: "flex-start"
          }}>
            <div style={{
              fontSize: "28px",
              width: "40px",
              height: "40px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              🤖
            </div>
            <div style={{
              padding: "12px 16px",
              borderRadius: "16px",
              background: "#f0f0f0",
              color: "#666"
            }}>
              ⏳ Gerando resposta...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* INPUT AREA */}
      <div style={{
        padding: "20px 30px",
        borderTop: "1px solid #e0e0e0",
        background: "#f9f9f9"
      }}>
        <form
          onSubmit={handleSend}
          style={{
            display: "flex",
            gap: "12px",
            maxWidth: "900px",
            margin: "0 auto"
          }}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite sua pergunta ou peça ajuda para preencher um template..."
            style={{
              flex: 1,
              padding: "12px 16px",
              border: "2px solid #e0e0e0",
              borderRadius: "24px",
              fontSize: "14px",
              outline: "none",
              transition: "border-color 0.2s",
              fontFamily: "inherit"
            }}
            onFocus={(e) => {
              e.target.style.borderColor = "#007bff";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = "#e0e0e0";
            }}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            style={{
              padding: "12px 28px",
              background: loading ? "#ccc" : "#007bff",
              color: "white",
              border: "none",
              borderRadius: "24px",
              cursor: loading ? "not-allowed" : "pointer",
              fontSize: "14px",
              fontWeight: "600",
              transition: "background-color 0.2s",
              whiteSpace: "nowrap"
            }}
            onMouseEnter={(e) => {
              if (!loading) e.target.style.background = "#0056cc";
            }}
            onMouseLeave={(e) => {
              if (!loading) e.target.style.background = "#007bff";
            }}
          >
            {loading ? "Aguarde..." : "Enviar"}
          </button>
        </form>
      </div>
    </div>
  );
}
