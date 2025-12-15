"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { MessageCircle, X, Send } from "lucide-react";
import { apiPost, getApiBase } from "@/lib/api";

export default function ChatWidget({ context = "" }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Handle custom event to open chat with a pre-filled question
  const handleOpenWithQuestion = useCallback((event) => {
    const { question } = event.detail || {};
    if (question) {
      setIsOpen(true);
      setInput(question);
      // Focus input after a brief delay to ensure DOM is updated
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, []);

  useEffect(() => {
    window.addEventListener("openChatWithQuestion", handleOpenWithQuestion);
    return () => {
      window.removeEventListener("openChatWithQuestion", handleOpenWithQuestion);
    };
  }, [handleOpenWithQuestion]);

  async function handleSend(e) {
    e?.preventDefault();
    if (!input.trim()) return;

    const question = input.trim();
    const contextualQuestion = context 
      ? `[Contexto: ${context}]\n\n${question}` 
      : question;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);

    try {
      const res = await apiPost("/chat/", { question: contextualQuestion });

      let answer = "";
      if (res?.data?.answer) {
        answer = res.data.answer;
      } else if (res?.answer) {
        answer = res.answer;
      } else {
        answer = JSON.stringify(res);
      }

      setMessages((prev) => [...prev, { role: "agent", text: answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "agent", text: `❌ Erro: ${err.message}` }
      ]);
    } finally {
      setLoading(false);
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="chat-widget-button"
        style={{
          position: "fixed",
          bottom: "24px",
          right: "24px",
          width: "60px",
          height: "60px",
          borderRadius: "50%",
          background: "var(--primary)",
          color: "#fff",
          border: "none",
          boxShadow: "0 4px 12px rgba(27, 166, 178, 0.3)",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "all 0.2s ease",
          zIndex: 1000
        }}
      >
        <MessageCircle size={28} />
      </button>
    );
  }

  return (
    <div
      className="chat-widget"
      style={{
        position: "fixed",
        bottom: "24px",
        right: "24px",
        width: "380px",
        height: "550px",
        background: "#fff",
        borderRadius: "18px",
        boxShadow: "0 8px 32px rgba(15, 92, 99, 0.2)",
        display: "flex",
        flexDirection: "column",
        zIndex: 1000,
        overflow: "hidden"
      }}
    >
      {/* Header */}
      <div
        style={{
          background: "var(--primary)",
          color: "#fff",
          padding: "16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <MessageCircle size={20} />
          <span style={{ fontWeight: 600 }}>TR4CTION Assistant</span>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          style={{
            background: "transparent",
            border: "none",
            color: "#fff",
            cursor: "pointer",
            padding: "4px"
          }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "12px"
        }}
      >
        {messages.length === 0 && (
          <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", textAlign: "center", marginTop: "20px" }}>
            👋 Olá! Estou aqui para ajudar no preenchimento do template.
            <br />
            <br />
            Pode me perguntar sobre qualquer campo!
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "80%"
            }}
          >
            <div
              style={{
                padding: "10px 14px",
                borderRadius: "12px",
                background: msg.role === "user" ? "var(--primary)" : "#f1f5f9",
                color: msg.role === "user" ? "#fff" : "var(--text-main)",
                fontSize: "0.9rem",
                lineHeight: "1.5",
                wordWrap: "break-word"
              }}
            >
              {msg.text}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ alignSelf: "flex-start", fontSize: "0.85rem", color: "var(--text-muted)" }}>
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSend}
        style={{
          padding: "16px",
          borderTop: "1px solid var(--border)",
          display: "flex",
          gap: "8px"
        }}
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Digite sua pergunta..."
          style={{
            flex: 1,
            padding: "10px 14px",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            fontSize: "0.9rem",
            outline: "none"
          }}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            width: "44px",
            height: "44px",
            borderRadius: "12px",
            background: input.trim() ? "var(--primary)" : "#e5e7eb",
            color: "#fff",
            border: "none",
            cursor: input.trim() ? "pointer" : "not-allowed",
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}
        >
          <Send size={18} />
        </button>
      </form>

      <style jsx>{`
        .typing-indicator {
          display: flex;
          gap: 4px;
          padding: 8px;
        }
        .typing-indicator span {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--text-muted);
          animation: typing 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) {
          animation-delay: 0.2s;
        }
        .typing-indicator span:nth-child(3) {
          animation-delay: 0.4s;
        }
        @keyframes typing {
          0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.7;
          }
          30% {
            transform: translateY(-10px);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}
