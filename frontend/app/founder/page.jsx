"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function FounderHome() {
  const { logout, user } = useAuth();

  return (
    <div>
      {/* Header com botão de logout */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h1 style={{ margin: 0 }}>Bem-vindo, {user?.full_name || "founder"} 👋</h1>
        <button 
          onClick={logout}
          style={{
            padding: "8px 16px",
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "8px",
            color: "#ef4444",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: "500",
            transition: "all 0.2s ease",
            display: "flex",
            alignItems: "center",
            gap: "6px"
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(239, 68, 68, 0.2)";
            e.currentTarget.style.borderColor = "#ef4444";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(239, 68, 68, 0.1)";
            e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
          }}
        >
          <span>🚪</span>
          Sair
        </button>
      </div>
      <p style={{ color: "var(--text-muted)", maxWidth: 620 }}>
        Use o agente para preencher os templates oficiais (ICP, Persona, SWOT,
        Funil, Conteúdo, KPIs) e acompanhar seu progresso ao longo do programa.
      </p>

      <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
        <Link href="/founder/chat">
          <button className="btn btn-primary">Começar pelo chat</button>
        </Link>
        <Link href="/founder/templates">
          <button className="btn btn-ghost">Ver templates</button>
        </Link>
        <Link href="/founder/dashboard">
          <button className="btn btn-ghost">Dashboard</button>
        </Link>
      </div>

      <div style={{ marginTop: 32 }}>
        <div className="card">
          <h3>Próximos Passos</h3>
          <ul style={{ fontSize: "0.9rem", lineHeight: 1.8 }}>
            <li>Definir ICP (Ideal Customer Profile)</li>
            <li>Criar Personas detalhadas</li>
            <li>Análise SWOT da startup</li>
            <li>Mapear funil de marketing</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
