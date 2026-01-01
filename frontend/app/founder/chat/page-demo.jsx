"use client";

import { useState } from "react";
import axios from "axios";
import styles from "./style.module.css";

export default function FounderDashboard() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState([
    {
      role: "agent",
      text: "Bem-vindo ao TR4CTION Agent! 🚀\n\nVocê pode:\n1. Fazer perguntas sobre marketing\n2. Preencher templates\n3. Gerar conteúdo com IA\n\nComo posso ajudar?"
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("chat");

  const backendBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  async function handleSend(e) {
    e?.preventDefault();
    if (!input.trim()) return;

    const question = input.trim();
    setInput("");
    setHistory((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);

    try {
      const res = await axios.post(
        `${backendBase}/chat/`,
        { question },
        { timeout: 30000 }
      );

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
      console.error("Erro:", err);
      const errorMsg = err.response?.data?.detail || err.message || "Erro ao comunicar com servidor";
      setHistory((prev) => [...prev, { role: "agent", text: `❌ Erro: ${errorMsg}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "20px" }}>
      <div style={{ display: "flex", gap: "20px", marginBottom: "30px" }}>
        <button
          onClick={() => setActiveTab("chat")}
          style={{
            padding: "10px 20px",
            background: activeTab === "chat" ? "#007bff" : "#f0f0f0",
            color: activeTab === "chat" ? "white" : "black",
            border: "none",
            cursor: "pointer",
            borderRadius: "4px",
            fontSize: "16px"
          }}
        >
          💬 Chat com IA
        </button>
        <button
          onClick={() => setActiveTab("templates")}
          style={{
            padding: "10px 20px",
            background: activeTab === "templates" ? "#007bff" : "#f0f0f0",
            color: activeTab === "templates" ? "white" : "black",
            border: "none",
            cursor: "pointer",
            borderRadius: "4px",
            fontSize: "16px"
          }}
        >
          📋 Templates
        </button>
        <button
          onClick={() => setActiveTab("widget")}
          style={{
            padding: "10px 20px",
            background: activeTab === "widget" ? "#007bff" : "#f0f0f0",
            color: activeTab === "widget" ? "white" : "black",
            border: "none",
            cursor: "pointer",
            borderRadius: "4px",
            fontSize: "16px"
          }}
        >
          🎛️ Widget
        </button>
      </div>

      {/* TAB: CHAT */}
      {activeTab === "chat" && (
        <div style={{
          border: "1px solid #ddd",
          borderRadius: "8px",
          padding: "20px",
          height: "600px",
          display: "flex",
          flexDirection: "column"
        }}>
          <div style={{
            flex: 1,
            overflowY: "auto",
            marginBottom: "20px",
            padding: "10px",
            background: "#f9f9f9",
            borderRadius: "4px"
          }}>
            {history.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  marginBottom: "12px",
                  padding: "10px",
                  borderRadius: "4px",
                  background: msg.role === "user" ? "#007bff" : "#e9ecef",
                  color: msg.role === "user" ? "white" : "black",
                  textAlign: msg.role === "user" ? "right" : "left"
                }}
              >
                <strong>{msg.role === "user" ? "Você" : "Agente"}:</strong>
                <p style={{ margin: "5px 0 0 0", whiteSpace: "pre-wrap" }}>{msg.text}</p>
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
                borderRadius: "4px",
                fontSize: "14px"
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
          <h2>📋 Templates Disponíveis</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "20px" }}>
            {[
              { title: "ICP + Persona", desc: "Ideal Customer Profile e Buyer Persona" },
              { title: "SWOT", desc: "Análise de Forças, Fraquezas, Oportunidades e Ameaças" },
              { title: "Go-to-Market", desc: "Estratégia de lançamento no mercado" },
              { title: "Pitch Deck", desc: "Apresentação para investidores" },
              { title: "Roadmap", desc: "Planejamento de produto" },
              { title: "Landing Page", desc: "Copy para página de captura" }
            ].map((template, idx) => (
              <div
                key={idx}
                style={{
                  border: "1px solid #ddd",
                  padding: "20px",
                  borderRadius: "8px",
                  cursor: "pointer",
                  transition: "all 0.3s",
                  background: "#f9f9f9",
                  ":hover": { background: "#f0f0f0" }
                }}
                onClick={() => {
                  setActiveTab("chat");
                  setInput(`Ajude-me a preencher o template: ${template.title}`);
                }}
              >
                <h3 style={{ margin: "0 0 10px 0" }}>{template.title}</h3>
                <p style={{ margin: 0, color: "#666", fontSize: "14px" }}>{template.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB: WIDGET */}
      {activeTab === "widget" && (
        <div>
          <h2>🎛️ Widget do Chatbot</h2>
          <div style={{
            border: "1px solid #ddd",
            borderRadius: "8px",
            padding: "20px",
            background: "#f9f9f9"
          }}>
            <p>O widget está pronto para ser integrado em seu site!</p>
            <pre style={{
              background: "#222",
              color: "#0f0",
              padding: "15px",
              borderRadius: "4px",
              overflow: "auto"
            }}>
{`<!-- Adicione isto no seu HTML -->
<script src="https://tr4ction-v2-agent.vercel.app/widget.js"></script>
<tr4ction-widget 
  backend="https://54.144.92.71.sslip.io"
  position="bottom-right"
/>

<!-- Ou use este código para teste local -->
<iframe 
  src="http://localhost:3000/widget" 
  style="position:fixed;bottom:20px;right:20px;width:400px;height:500px;border:none;border-radius:8px;box-shadow:0 5px 40px rgba(0,0,0,0.16)"
/>
`}
            </pre>
            <p style={{ marginTop: "20px", color: "#666" }}>
              O widget pode ser customizado com cores, posição e mensagens.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
