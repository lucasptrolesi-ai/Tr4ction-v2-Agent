"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import axios from "axios";

// Ícones SVG corporativos
const LogoIcon = () => (
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#00BCD4" />
        <stop offset="100%" stopColor="#00ACC1" />
      </linearGradient>
    </defs>
    <rect width="32" height="32" rx="8" fill="url(#logoGrad)"/>
    <path d="M8 12L16 8L24 12V20L16 24L8 20V12Z" stroke="white" strokeWidth="1.5" fill="none"/>
    <path d="M16 8V24M8 12L24 20M24 12L8 20" stroke="white" strokeWidth="1.5" opacity="0.6"/>
    <circle cx="16" cy="16" r="3" fill="white"/>
  </svg>
);

const BotIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="3" y="6" width="18" height="14" rx="3" stroke="currentColor" strokeWidth="1.5"/>
    <circle cx="8.5" cy="13" r="1.5" fill="currentColor"/>
    <circle cx="15.5" cy="13" r="1.5" fill="currentColor"/>
    <path d="M9 17H15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    <path d="M12 6V3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    <circle cx="12" cy="2" r="1" fill="currentColor"/>
  </svg>
);

const UserIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.5"/>
    <path d="M4 20C4 16.6863 6.68629 14 10 14H14C17.3137 14 20 16.6863 20 20V21H4V20Z" stroke="currentColor" strokeWidth="1.5"/>
  </svg>
);

const SendIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const SparkleIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 0L14.59 8.41L23 12L14.59 15.59L12 24L9.41 15.59L1 12L9.41 8.41L12 0Z"/>
  </svg>
);

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState([
    {
      role: "agent",
      text: "Olá! Sou o **Assistente TR4CTION**, sua IA especializada em estratégias de startup.\n\nEstou pronto para ajudá-lo a construir:\n\n• **ICP + Persona** — Defina seu cliente ideal com precisão\n• **Análise SWOT** — Mapeie forças, fraquezas, oportunidades e ameaças\n• **Go-to-Market** — Estruture sua entrada no mercado\n• **Pitch Deck** — Apresentação para investidores\n• **Roadmap** — Planejamento estratégico do produto\n• **Landing Page** — Copy e estrutura de conversão\n\nComo posso ajudá-lo hoje?"
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);
  const messagesEndRef = useRef(null);

  const backendBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [history]);

  // Formatar texto com **bold** e listas
  const formatMessage = (text) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i} style={{ fontWeight: 600 }}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

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
      setHistory((prev) => [...prev, { role: "agent", text: `Desculpe, ocorreu um erro: ${errorMessage}\n\nVerifique se o backend está rodando em ${backendBase}` }]);
    } finally {
      setLoading(false);
    }
  }, [input, backendBase]);

  const styles = {
    container: {
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)",
      fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
    },
    header: {
      padding: "16px 32px",
      background: "rgba(15, 23, 42, 0.8)",
      backdropFilter: "blur(20px)",
      borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
    },
    headerLeft: {
      display: "flex",
      alignItems: "center",
      gap: "16px",
    },
    logoContainer: {
      display: "flex",
      alignItems: "center",
      gap: "12px",
    },
    title: {
      margin: 0,
      fontSize: "20px",
      fontWeight: "700",
      background: "linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%)",
      WebkitBackgroundClip: "text",
      WebkitTextFillColor: "transparent",
      letterSpacing: "-0.02em",
    },
    subtitle: {
      margin: 0,
      fontSize: "13px",
      color: "#64748b",
      fontWeight: "400",
    },
    statusBadge: {
      display: "flex",
      alignItems: "center",
      gap: "8px",
      padding: "6px 14px",
      background: "rgba(34, 197, 94, 0.1)",
      border: "1px solid rgba(34, 197, 94, 0.2)",
      borderRadius: "999px",
      fontSize: "12px",
      color: "#22c55e",
      fontWeight: "500",
    },
    statusDot: {
      width: "8px",
      height: "8px",
      background: "#22c55e",
      borderRadius: "50%",
      boxShadow: "0 0 8px #22c55e",
      animation: "pulse 2s infinite",
    },
    chatArea: {
      flex: 1,
      overflowY: "auto",
      padding: "32px",
      display: "flex",
      flexDirection: "column",
      gap: "24px",
    },
    messagesContainer: {
      maxWidth: "900px",
      width: "100%",
      margin: "0 auto",
      display: "flex",
      flexDirection: "column",
      gap: "24px",
    },
    messageRow: (isUser) => ({
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      gap: "12px",
      animation: "fadeInUp 0.3s ease-out",
    }),
    avatar: (isUser) => ({
      width: "40px",
      height: "40px",
      borderRadius: "12px",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0,
      background: isUser 
          ? "linear-gradient(135deg, #00BCD4 0%, #00ACC1 100%)"
          : "linear-gradient(135deg, #26C6DA 0%, #00BCD4 100%)",
      color: "white",
      boxShadow: isUser
          ? "0 4px 14px rgba(0, 188, 212, 0.4)"
          : "0 4px 14px rgba(38, 198, 218, 0.4)",
    }),
    messageBubble: (isUser) => ({
      maxWidth: "70%",
      padding: "16px 20px",
      borderRadius: isUser ? "20px 20px 4px 20px" : "20px 20px 20px 4px",
      background: isUser 
        ? "linear-gradient(135deg, #00BCD4 0%, #00ACC1 100%)"
        : "rgba(255, 255, 255, 0.05)",
      color: isUser ? "#ffffff" : "#e2e8f0",
      lineHeight: "1.6",
      whiteSpace: "pre-wrap",
      wordWrap: "break-word",
      fontSize: "14px",
      border: isUser ? "none" : "1px solid rgba(255, 255, 255, 0.08)",
      backdropFilter: isUser ? "none" : "blur(10px)",
      boxShadow: isUser 
        ? "0 4px 20px rgba(0, 188, 212, 0.3)"
        : "0 4px 20px rgba(0, 0, 0, 0.2)",
    }),
    loadingBubble: {
      display: "flex",
      alignItems: "center",
      gap: "12px",
      padding: "16px 20px",
      borderRadius: "20px 20px 20px 4px",
      background: "rgba(255, 255, 255, 0.05)",
      border: "1px solid rgba(255, 255, 255, 0.08)",
      backdropFilter: "blur(10px)",
    },
    loadingDots: {
      display: "flex",
      gap: "4px",
    },
    loadingDot: (delay) => ({
      width: "8px",
      height: "8px",
      borderRadius: "50%",
      background: "#00BCD4",
      animation: `bounce 1.4s infinite ease-in-out both`,
      animationDelay: delay,
    }),
    inputArea: {
      padding: "20px 32px 28px",
      background: "rgba(15, 23, 42, 0.9)",
      backdropFilter: "blur(20px)",
      borderTop: "1px solid rgba(255, 255, 255, 0.08)",
    },
    inputContainer: {
      maxWidth: "900px",
      margin: "0 auto",
    },
    inputWrapper: {
      display: "flex",
      gap: "12px",
      padding: "8px",
      background: inputFocused 
        ? "rgba(255, 255, 255, 0.08)" 
        : "rgba(255, 255, 255, 0.04)",
      borderRadius: "16px",
      border: inputFocused 
        ? "1px solid rgba(0, 188, 212, 0.5)"
        : "1px solid rgba(255, 255, 255, 0.08)",
      transition: "all 0.2s ease",
      boxShadow: inputFocused 
        ? "0 0 0 4px rgba(0, 188, 212, 0.1), 0 4px 20px rgba(0, 0, 0, 0.3)"
        : "0 4px 20px rgba(0, 0, 0, 0.2)",
    },
    input: {
      flex: 1,
      padding: "12px 16px",
      background: "transparent",
      border: "none",
      fontSize: "15px",
      color: "#f1f5f9",
      outline: "none",
      fontFamily: "inherit",
    },
    sendButton: {
      padding: "12px 24px",
      background: loading 
        ? "rgba(100, 116, 139, 0.5)"
        : "linear-gradient(135deg, #00BCD4 0%, #00ACC1 100%)",
      color: "white",
      border: "none",
      borderRadius: "12px",
      cursor: loading ? "not-allowed" : "pointer",
      fontSize: "14px",
      fontWeight: "600",
      display: "flex",
      alignItems: "center",
      gap: "8px",
      transition: "all 0.2s ease",
      boxShadow: loading 
        ? "none"
        : "0 4px 14px rgba(0, 188, 212, 0.4)",
    },
    hint: {
      marginTop: "12px",
      textAlign: "center",
      fontSize: "12px",
      color: "#64748b",
    },
    sparkle: {
      color: "#fbbf24",
      marginRight: "4px",
    },
  };

  return (
    <>
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes bounce {
          0%, 80%, 100% {
            transform: scale(0);
          }
          40% {
            transform: scale(1);
          }
        }
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
        input::placeholder {
          color: #64748b;
        }
        ::-webkit-scrollbar {
          width: 6px;
        }
        ::-webkit-scrollbar-track {
          background: transparent;
        }
        ::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      `}</style>
      
      <div style={styles.container}>
        {/* HEADER */}
        <header style={styles.header}>
          <div style={styles.headerLeft}>
            <div style={styles.logoContainer}>
              <LogoIcon />
              <div>
                <h1 style={styles.title}>TR4CTION Agent</h1>
                <p style={styles.subtitle}>Assistente de Estratégia para Startups</p>
              </div>
            </div>
          </div>
          <div style={styles.statusBadge}>
            <div style={styles.statusDot}></div>
            AI Online
          </div>
        </header>

        {/* CHAT MESSAGES */}
        <div style={styles.chatArea}>
          <div style={styles.messagesContainer}>
            {history.map((msg, idx) => (
              <div key={idx} style={styles.messageRow(msg.role === "user")}>
                {msg.role === "agent" && (
                  <div style={styles.avatar(false)}>
                    <BotIcon />
                  </div>
                )}
                
                <div style={styles.messageBubble(msg.role === "user")}>
                  {formatMessage(msg.text)}
                </div>

                {msg.role === "user" && (
                  <div style={styles.avatar(true)}>
                    <UserIcon />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div style={styles.messageRow(false)}>
                <div style={styles.avatar(false)}>
                  <BotIcon />
                </div>
                <div style={styles.loadingBubble}>
                  <div style={styles.loadingDots}>
                    <div style={styles.loadingDot("0s")}></div>
                    <div style={styles.loadingDot("0.16s")}></div>
                    <div style={styles.loadingDot("0.32s")}></div>
                  </div>
                  <span style={{ color: "#94a3b8", fontSize: "14px" }}>Analisando...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* INPUT AREA */}
        <div style={styles.inputArea}>
          <div style={styles.inputContainer}>
            <form onSubmit={handleSend} style={styles.inputWrapper}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onFocus={() => setInputFocused(true)}
                onBlur={() => setInputFocused(false)}
                placeholder="Digite sua mensagem ou peça ajuda com um template..."
                style={styles.input}
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                style={{
                  ...styles.sendButton,
                  opacity: !input.trim() && !loading ? 0.5 : 1,
                }}
              >
                <SendIcon />
                {loading ? "Enviando..." : "Enviar"}
              </button>
            </form>
            <p style={styles.hint}>
              <span style={styles.sparkle}><SparkleIcon /></span>
              Powered by TR4CTION AI • Metodologia FCJ Venture Builder
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
