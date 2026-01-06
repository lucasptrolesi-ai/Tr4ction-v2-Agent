"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import Link from "next/link";

const LogoIcon = () => (
  <svg width="56" height="56" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#00BCD4" />
        <stop offset="100%" stopColor="#00ACC1" />
      </linearGradient>
    </defs>
    <rect width="56" height="56" rx="16" fill="url(#logoGradient)" />
    <path d="M14 21L28 14L42 21V35L28 42L14 35V21Z" stroke="white" strokeWidth="2.5" fill="none" />
    <path d="M28 14V42M14 21L42 35M42 21L14 35" stroke="white" strokeWidth="2.5" opacity="0.5" />
    <circle cx="28" cy="28" r="5" fill="white" />
  </svg>
);

const EmailIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M4 4H20C21.1 4 22 4.9 22 6V18C22 19.1 21.1 20 20 20H4C2.9 20 2 19.1 2 18V6C2 4.9 2.9 4 4 4Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M22 6L12 13L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const LockIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="5" y="11" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="2" />
    <path d="M7 11V7C7 4.79086 8.79086 3 11 3H13C15.2091 3 17 4.79086 17 7V11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <circle cx="12" cy="16" r="1.5" fill="currentColor" />
  </svg>
);

const SparkleIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 0L14.59 8.41L23 12L14.59 15.59L12 24L9.41 15.59L1 12L9.41 8.41L12 0Z" opacity="0.7" />
  </svg>
);

export default function LoginPage() {
  const { login, loading: authLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [focusedField, setFocusedField] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message || "Erro ao fazer login");
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)",
        color: "#e2e8f0",
      }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "48px",
            height: "48px",
            border: "4px solid rgba(0, 188, 212, 0.2)",
            borderTopColor: "#00BCD4",
            borderRadius: "50%",
            animation: "spin 1s linear infinite",
          }}></div>
          <span>Carregando...</span>
        </div>
        <style>{`
          @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        `}</style>
      </div>
    );
  }

  return (
    <>
      <style>{`
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-8px); } }
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>

      <div style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)",
        color: "#e2e8f0",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "32px 16px",
      }}>
        <div style={{
          width: "100%",
          maxWidth: "1100px",
          display: "grid",
          gridTemplateColumns: "1.2fr 1fr",
          gap: "24px",
          background: "rgba(15, 23, 42, 0.8)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "20px",
          padding: "28px",
          boxShadow: "0 20px 60px rgba(0, 0, 0, 0.35)",
          backdropFilter: "blur(18px)",
        }}>
          <div style={{ position: "relative", overflow: "hidden", borderRadius: "16px", background: "linear-gradient(160deg, rgba(0,188,212,0.15) 0%, rgba(0,172,193,0.1) 60%, rgba(14,165,233,0.08) 100%)", padding: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
              <div style={{ width: "48px", height: "48px", borderRadius: "12px", background: "linear-gradient(135deg, #00BCD4 0%, #00ACC1 100%)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 12px 30px rgba(0, 188, 212, 0.35)" }}>
                <LogoIcon />
              </div>
              <div>
                <h1 style={{ margin: 0, fontSize: "20px", fontWeight: 700 }}>TR4CTION - FCJ</h1>
                <p style={{ margin: 0, color: "#94a3b8", fontSize: "13px" }}>Plataforma Corporate Venture Builder</p>
              </div>
            </div>
            <div style={{ display: "grid", gap: "16px", animation: "fadeInUp 0.4s ease" }}>
              {["Conhecimento da FCJ centralizado", "Onboarding guiado para founders", "Documentos indexados com IA", "Metricas em tempo real"].map((item, idx) => (
                <div key={idx} style={{ display: "flex", gap: "12px", alignItems: "flex-start", padding: "12px", borderRadius: "12px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <div style={{ width: "32px", height: "32px", borderRadius: "10px", background: "linear-gradient(135deg, #00BCD4 0%, #26C6DA 100%)", display: "flex", alignItems: "center", justifyContent: "center", color: "#0b1224", fontWeight: 700 }}>
                    <SparkleIcon />
                  </div>
                  <div style={{ fontSize: "14px", color: "#e2e8f0", lineHeight: "1.5" }}>{item}</div>
                </div>
              ))}
            </div>
            <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
              <div style={{ position: "absolute", width: "220px", height: "220px", background: "radial-gradient(circle, rgba(0,188,212,0.12) 0%, transparent 70%)", top: "-40px", right: "-40px", filter: "blur(6px)", animation: "float 6s ease-in-out infinite" }}></div>
              <div style={{ position: "absolute", width: "180px", height: "180px", background: "radial-gradient(circle, rgba(38,198,218,0.12) 0%, transparent 70%)", bottom: "-30px", left: "-20px", filter: "blur(6px)", animation: "float 7s ease-in-out infinite", animationDelay: "1s" }}></div>
            </div>
          </div>

          <div style={{ background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "16px", padding: "24px", boxShadow: "0 12px 32px rgba(0,0,0,0.25)", animation: "fadeInUp 0.4s ease" }}>
            <div style={{ marginBottom: "16px" }}>
              <p style={{ margin: 0, fontSize: "13px", color: "#94a3b8" }}>Acesse com seu email corporativo</p>
              <h2 style={{ margin: "6px 0 0", fontSize: "24px", fontWeight: 700, color: "#f8fafc" }}>Entrar</h2>
            </div>

            <form onSubmit={handleSubmit} style={{ display: "grid", gap: "14px" }}>
              <label style={{ display: "grid", gap: "6px", fontSize: "13px", color: "#94a3b8" }}>
                <span style={{ display: "flex", alignItems: "center", gap: "8px", color: focusedField === "email" ? "#00BCD4" : "#94a3b8" }}>
                  <EmailIcon /> Email
                </span>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", padding: "12px 14px", borderRadius: "12px", border: `1px solid ${focusedField === "email" ? "rgba(0, 188, 212, 0.5)" : "rgba(255, 255, 255, 0.1)"}`, background: "rgba(255, 255, 255, 0.02)", boxShadow: focusedField === "email" ? "0 0 0 4px rgba(0, 188, 212, 0.08)" : "none" }}>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onFocus={() => setFocusedField("email")}
                    onBlur={() => setFocusedField(null)}
                    placeholder="seu.email@fcj.com"
                    required
                    style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: "#f8fafc", fontSize: "15px" }}
                  />
                </div>
              </label>

              <label style={{ display: "grid", gap: "6px", fontSize: "13px", color: "#94a3b8" }}>
                <span style={{ display: "flex", alignItems: "center", gap: "8px", color: focusedField === "password" ? "#00BCD4" : "#94a3b8" }}>
                  <LockIcon /> Senha
                </span>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", padding: "12px 14px", borderRadius: "12px", border: `1px solid ${focusedField === "password" ? "rgba(0, 188, 212, 0.5)" : "rgba(255, 255, 255, 0.1)"}`, background: "rgba(255, 255, 255, 0.02)", boxShadow: focusedField === "password" ? "0 0 0 4px rgba(0, 188, 212, 0.08)" : "none" }}>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setFocusedField("password")}
                    onBlur={() => setFocusedField(null)}
                    placeholder="********"
                    required
                    style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: "#f8fafc", fontSize: "15px" }}
                  />
                </div>
              </label>

              {error && (
                <div style={{ color: "#f87171", fontSize: "13px", padding: "10px 12px", background: "rgba(248,113,113,0.12)", borderRadius: "10px", border: "1px solid rgba(248,113,113,0.4)" }}>
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                style={{
                  marginTop: "4px",
                  width: "100%",
                  padding: "14px",
                  border: "none",
                  borderRadius: "12px",
                  background: loading ? "rgba(100,116,139,0.5)" : "linear-gradient(135deg, #00BCD4 0%, #00ACC1 100%)",
                  color: "#0b1224",
                  fontWeight: 700,
                  fontSize: "15px",
                  cursor: loading ? "not-allowed" : "pointer",
                  boxShadow: loading ? "none" : "0 12px 32px rgba(0,188,212,0.4)",
                  transition: "all 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  if (!loading) {
                    e.currentTarget.style.boxShadow = "0 16px 36px rgba(0,188,212,0.5)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!loading) {
                    e.currentTarget.style.boxShadow = "0 12px 32px rgba(0,188,212,0.4)";
                  }
                }}
              >
                {loading ? "Entrando..." : "Entrar"}
              </button>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "13px", color: "#94a3b8" }}>
                <Link href="/admin/knowledge" style={{ color: "#00BCD4", fontWeight: 600 }}>Area Admin</Link>
                <Link href="/founder" style={{ color: "#26C6DA", fontWeight: 600 }}>Area Founder</Link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
