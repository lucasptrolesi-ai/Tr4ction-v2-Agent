"use client";

import { useState, useCallback } from "react";
import axios from "axios";

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState([
    {
      role: "agent",
      text: "Bem-vindo ao TR4CTION Agent! 🚀\n\nVocê pode fazer perguntas sobre marketing, templates e estratégia. Como posso ajudar?"
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("chat");

  const backendBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

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
      setHistory((prev) => [...prev, { role: "agent", text: `❌ Erro: ${errorMessage}` }]);
    } finally {
      setLoading(false);
    }
  }, [input, backendBase]);

  return (
    <div style={{ maxWidth: "860px", margin: "0 auto", padding: "30px" }}>
      <h1>TR4CTION Agent</h1>

      {/* TABS */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "30px", borderBottom: "1px solid #ddd", paddingBottom: "10px" }}>
        <button
          onClick={() => setActiveTab("chat")}
          style={{
            padding: "8px 16px",
            background: "none",
            border: "none",
            borderBottom: activeTab === "chat" ? "3px solid #007bff" : "none",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: activeTab === "chat" ? "bold" : "normal"
          }}
        >
          💬 Chat
        </button>
        <button
          onClick={() => setActiveTab("templates")}
          style={{
            padding: "8px 16px",
            background: "none",
            border: "none",
            borderBottom: activeTab === "templates" ? "3px solid #007bff" : "none",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: activeTab === "templates" ? "bold" : "normal"
          }}
        >
          📋 Templates
        </button>
        <button
          onClick={() => setActiveTab("widget")}
          style={{
            padding: "8px 16px",
            background: "none",
            border: "none",
            borderBottom: activeTab === "widget" ? "3px solid #007bff" : "none",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: activeTab === "widget" ? "bold" : "normal"
          }}
        >
          🎛️ Widget
        </button>
      </div>

      {/* TAB: CHAT */}
      {activeTab === "chat" && (
        <div>
          <div
            style={{
              border: "1px solid #ddd",
              borderRadius: "8px",
              padding: "16px",
              minHeight: "400px",
              maxHeight: "500px",
              overflowY: "auto",
              marginBottom: "16px",
              background: "#f9f9f9"
            }}
          >
            {history.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  marginBottom: "12px",
                  textAlign: msg.role === "user" ? "right" : "left"
                }}
              >
                <div
                  style={{
                    display: "inline-block",
                    padding: "10px 14px",
                    borderRadius: "8px",
                    background: msg.role === "user" ? "#007bff" : "#e9ecef",
                    color: msg.role === "user" ? "white" : "black",
                    maxWidth: "70%",
                    wordWrap: "break-word"
                  }}
                >
                  <strong>{msg.role === "user" ? "Você" : "Agente"}:</strong>
                  <p style={{ margin: "5px 0 0 0", whiteSpace: "pre-wrap" }}>{msg.text}</p>
                </div>
              </div>
            ))}
            {loading && <div style={{ color: "#999" }}>⏳ Gerando resposta...</div>}
          </div>

          <form
            onSubmit={handleSend}
            style={{
              display: "flex",
              gap: "10px"
            }}
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Digite sua pergunta..."
              style={{
                flex: 1,
                padding: "10px",
                border: "1px solid #ddd",
                borderRadius: "4px",
                fontSize: "14px"
              }}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading}
              style={{
                padding: "10px 20px",
                background: loading ? "#ccc" : "#007bff",
                color: "white",
                border: "none",
                cursor: loading ? "not-allowed" : "pointer",
                borderRadius: "4px"
              }}
            >
              {loading ? "Aguarde..." : "Enviar"}
            </button>
          </form>
        </div>
      )}

      {/* TAB: TEMPLATES */}
      {activeTab === "templates" && (
        <div>
          <p style={{ color: "#666", marginBottom: "20px" }}>
            Clique em qualquer template para preencher com ajuda da IA
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "15px" }}>
            {[
              { title: "ICP + Persona", emoji: "👥", desc: "Ideal Customer Profile" },
              { title: "SWOT", emoji: "💎", desc: "Análise de Mercado" },
              { title: "Go-to-Market", emoji: "🎯", desc: "Estratégia de Lançamento" },
              { title: "Pitch Deck", emoji: "📊", desc: "Para Investidores" },
              { title: "Roadmap", emoji: "🗺️", desc: "Planejamento" },
              { title: "Landing Page", emoji: "📱", desc: "Copy & Design" }
            ].map((template, idx) => (
              <div
                key={idx}
                onClick={() => {
                  setActiveTab("chat");
                  setInput(`Ajude-me a preencher: ${template.title}`);
                }}
                style={{
                  border: "1px solid #ddd",
                  padding: "16px",
                  borderRadius: "8px",
                  cursor: "pointer",
                  background: "#f9f9f9",
                  transition: "all 0.2s",
                  textAlign: "center"
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "#f0f0f0";
                  e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.1)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "#f9f9f9";
                  e.currentTarget.style.boxShadow = "none";
                }}
              >
                <div style={{ fontSize: "32px", marginBottom: "8px" }}>{template.emoji}</div>
                <h3 style={{ margin: "0 0 5px 0", fontSize: "16px" }}>{template.title}</h3>
                <p style={{ margin: 0, color: "#666", fontSize: "13px" }}>{template.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB: WIDGET */}
      {activeTab === "widget" && (
        <div>
          <div style={{ background: "#f0f7ff", padding: "20px", borderRadius: "8px", marginBottom: "20px" }}>
            <h2 style={{ margin: "0 0 10px 0" }}>🎛️ Widget do Chatbot</h2>
            <p>Integre o chatbot em seu site com uma única linha!</p>
          </div>

          <h3>Código para Integração</h3>
          <pre style={{
            background: "#222",
            color: "#0f0",
            padding: "15px",
            borderRadius: "4px",
            overflow: "auto",
            fontSize: "12px"
          }}>
{`<!-- Adicione isto no seu website -->
<iframe 
  src="https://tr4ction-v2-agent.vercel.app/chat" 
  style="position:fixed;bottom:20px;right:20px;width:400px;height:500px;border:none;border-radius:12px;box-shadow:0 5px 40px rgba(0,0,0,0.16);z-index:9999"
/>

<!-- Ou use o script tag -->
<script src="https://tr4ction-v2-agent.vercel.app/widget.js"><\/script>
<tr4ction-widget backend="https://54.144.92.71.sslip.io" />
`}
          </pre>

          <h3 style={{ marginTop: "20px" }}>Customizações Disponíveis</h3>
          <ul style={{ color: "#666", lineHeight: "1.8" }}>
            <li>✅ Cor do tema (primary, secondary, dark)</li>
            <li>✅ Posição (bottom-right, bottom-left, top-right)</li>
            <li>✅ Mensagem inicial customizável</li>
            <li>✅ Avatar da IA</li>
            <li>✅ Integração com seu backend</li>
          </ul>
        </div>
      )}
    </div>
  );
}
