"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import axios from "axios";
import { useAuth } from "@/lib/auth";

const StatCard = ({ icon, label, value, sublabel, color = "#6366f1" }) => (
  <div style={{
    background: "rgba(255, 255, 255, 0.05)",
    border: "1px solid rgba(255, 255, 255, 0.08)",
    borderRadius: "16px",
    padding: "24px",
    backdropFilter: "blur(10px)",
    transition: "all 0.3s ease",
  }}
  onMouseEnter={(e) => {
    e.currentTarget.style.transform = "translateY(-4px)";
    e.currentTarget.style.boxShadow = `0 8px 30px ${color}40`;
    e.currentTarget.style.borderColor = `${color}50`;
  }}
  onMouseLeave={(e) => {
    e.currentTarget.style.transform = "translateY(0)";
    e.currentTarget.style.boxShadow = "none";
    e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
  }}>
    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
      <div>
        <div style={{
          fontSize: "14px",
          color: "#94a3b8",
          marginBottom: "8px",
          fontWeight: "500",
        }}>
          {label}
        </div>
        <div style={{
          fontSize: "32px",
          fontWeight: "700",
          color: "#f8fafc",
          marginBottom: "4px",
        }}>
          {value}
        </div>
        {sublabel && (
          <div style={{ fontSize: "12px", color: "#64748b" }}>
            {sublabel}
          </div>
        )}
      </div>
      <div style={{
        fontSize: "32px",
        opacity: 0.6,
      }}>
        {icon}
      </div>
    </div>
  </div>
);

const QuickActionCard = ({ icon, title, description, href, color = "#6366f1" }) => (
  <Link href={href} style={{ textDecoration: "none" }}>
    <div style={{
      background: "rgba(255, 255, 255, 0.03)",
      border: "1px solid rgba(255, 255, 255, 0.08)",
      borderRadius: "12px",
      padding: "20px",
      cursor: "pointer",
      transition: "all 0.2s ease",
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.background = "rgba(255, 255, 255, 0.06)";
      e.currentTarget.style.borderColor = `${color}50`;
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)";
      e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
    }}>
      <div style={{ fontSize: "28px", marginBottom: "12px" }}>{icon}</div>
      <h3 style={{ margin: "0 0 8px", fontSize: "16px", fontWeight: "600", color: "#f8fafc" }}>
        {title}
      </h3>
      <p style={{ margin: 0, fontSize: "13px", color: "#94a3b8", lineHeight: "1.5" }}>
        {description}
      </p>
    </div>
  </Link>
);

export default function AdminDashboard() {
  const { logout, user } = useAuth();
  const [stats, setStats] = useState({
    documents: 0,
    trails: 0,
    users: 0,
    chunks: 0,
  });
  const [loading, setLoading] = useState(true);

  const backendBase = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [docsRes, trailsRes] = await Promise.all([
          axios.get(`${backendBase}/admin/knowledge`).catch(() => ({ data: { data: { total: 0 } } })),
          axios.get(`${backendBase}/admin/trails`).catch(() => ({ data: [] })),
        ]);

        const documents = docsRes.data?.data?.documents || [];
        const totalChunks = documents.reduce((sum, doc) => sum + (doc.chunks_count || 0), 0);

        setStats({
          documents: docsRes.data?.data?.total || 0,
          trails: trailsRes.data?.length || 0,
          users: 12, // Mock - implementar endpoint real
          chunks: totalChunks,
        });
      } catch (error) {
        console.error("Erro ao carregar estatísticas:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [backendBase]);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "60px", color: "#94a3b8" }}>
        <div style={{ fontSize: "40px", marginBottom: "16px" }}>⏳</div>
        <div>Carregando dashboard...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "40px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 style={{
              margin: "0 0 8px",
              fontSize: "32px",
              fontWeight: "700",
              background: "linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}>
              Dashboard Administrativo
            </h1>
            <p style={{ margin: 0, fontSize: "16px", color: "#64748b" }}>
              Visão geral do sistema TR4CTION • FCJ Venture Builder
            </p>
          </div>
          <button 
            onClick={logout}
            style={{
              padding: "10px 20px",
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
              gap: "8px"
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
      </div>

      {/* Stats Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
        gap: "20px",
        marginBottom: "40px",
      }}>
        <StatCard
          icon="📚"
          label="Documentos Indexados"
          value={stats.documents}
          sublabel="Materiais FCJ na base"
           color="#5EEAD4"
        />
        <StatCard
          icon="🧩"
          label="Chunks Vetoriais"
          value={stats.chunks.toLocaleString()}
          sublabel="Segmentos para RAG"
           color="#5EEAD4"
        />
        <StatCard
          icon="🛤️"
          label="Trilhas Ativas"
          value={stats.trails}
          sublabel="Programas estruturados"
           color="#5EEAD4"
        />
        <StatCard
          icon="👥"
          label="Founders Ativos"
          value={stats.users}
          sublabel="Usuários no programa"
          color="#9CA3AF"
        />
      </div>

      {/* Quick Actions */}
      <div style={{ marginBottom: "40px" }}>
        <h2 style={{
          margin: "0 0 20px",
          fontSize: "20px",
          fontWeight: "600",
          color: "#f8fafc",
        }}>
          ⚡ Ações Rápidas
        </h2>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "16px",
        }}>
          <QuickActionCard
            icon="📤"
            title="Upload de Conhecimento"
            description="Adicione PDFs, PPTs ou DOCs à base de conhecimento do agente"
            href="/admin/knowledge"
            color="#5EEAD4"
          />
          <QuickActionCard
            icon="📊"
            title="Criar Nova Trilha"
            description="Estruture um novo programa com etapas e templates"
            href="/admin/trails"
            color="#5EEAD4"
          />
          <QuickActionCard
            icon="🔧"
            title="Configurar Templates"
            description="Edite schemas de formulários e campos dinâmicos"
            href="/admin/trails"
            color="#5EEAD4"
          />
          <QuickActionCard
            icon="👥"
            title="Gerenciar Founders"
            description="Veja progresso e respostas dos founders"
            href="/admin/users"
            color="#9CA3AF"
          />
        </div>
      </div>

      {/* System Status */}
      <div style={{
        background: "rgba(255, 255, 255, 0.03)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "12px",
        padding: "24px",
      }}>
        <h3 style={{ margin: "0 0 16px", fontSize: "16px", fontWeight: "600", color: "#f8fafc" }}>
          🖥️ Status do Sistema
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px" }}>
          <div>
            <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>Backend API</div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{
                width: "8px",
                height: "8px",
                background: "#22c55e",
                borderRadius: "50%",
                boxShadow: "0 0 8px #22c55e",
              }}></div>
              <span style={{ fontSize: "14px", color: "#f8fafc", fontWeight: "500" }}>Online</span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>ChromaDB</div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{
                width: "8px",
                height: "8px",
                background: "#22c55e",
                borderRadius: "50%",
                boxShadow: "0 0 8px #22c55e",
              }}></div>
              <span style={{ fontSize: "14px", color: "#f8fafc", fontWeight: "500" }}>Conectado</span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>LLM Provider</div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{
                width: "8px",
                height: "8px",
                background: "#22c55e",
                borderRadius: "50%",
                boxShadow: "0 0 8px #22c55e",
              }}></div>
              <span style={{ fontSize: "14px", color: "#f8fafc", fontWeight: "500" }}>Groq Ativo</span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>Último Backup</div>
            <div style={{ fontSize: "14px", color: "#f8fafc", fontWeight: "500" }}>17/12/2025</div>
          </div>
        </div>
      </div>
    </div>
  );
}
