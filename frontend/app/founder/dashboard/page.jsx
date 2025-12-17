"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { 
  CheckCircle, Clock, Lock, TrendingUp, 
  ChevronRight, RefreshCw, BarChart3, Target,
  LogOut
} from "lucide-react";
import { apiGet } from "@/lib/api";
import { useAuth } from "@/lib/auth";

// Componente de card de etapa
function StepCard({ step, trailId, onClick }) {
  const getStatusIcon = () => {
    if (step.locked) return <Lock size={20} style={{ color: "#94a3b8" }} />;
    if (step.completed) return <CheckCircle size={20} style={{ color: "#10b981" }} />;
    if (step.progress > 0) return <Clock size={20} style={{ color: "#f59e0b" }} />;
    return <Target size={20} style={{ color: "#3b82f6" }} />;
  };

  const getStatusLabel = () => {
    if (step.locked) return "Bloqueada";
    if (step.completed) return "Concluída";
    if (step.progress > 0) return "Em andamento";
    return "Não iniciada";
  };

  const getStatusColor = () => {
    if (step.locked) return "#94a3b8";
    if (step.completed) return "#10b981";
    if (step.progress > 0) return "#f59e0b";
    return "#3b82f6";
  };

  const getProgressColor = () => {
    if (step.progress >= 100) return "#10b981";
    if (step.progress >= 50) return "#f59e0b";
    if (step.progress > 0) return "#3b82f6";
    return "#e5e7eb";
  };

  return (
    <div
      className="card"
      onClick={!step.locked ? onClick : undefined}
      style={{
        cursor: step.locked ? "not-allowed" : "pointer",
        opacity: step.locked ? 0.6 : 1,
        transition: "all 0.2s",
        border: step.completed ? "2px solid #10b981" : "1px solid var(--border)"
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          <div style={{ 
            display: "flex", 
            alignItems: "center", 
            gap: "10px",
            marginBottom: "8px"
          }}>
            {getStatusIcon()}
            <span className="card-title" style={{ margin: 0 }}>{step.name}</span>
          </div>
          
          <div style={{ 
            fontSize: "0.8rem", 
            color: getStatusColor(),
            fontWeight: 500,
            marginBottom: "12px"
          }}>
            {getStatusLabel()}
          </div>

          {/* Barra de progresso */}
          <div style={{
            height: "6px",
            background: "#e5e7eb",
            borderRadius: "3px",
            overflow: "hidden",
            marginBottom: "8px"
          }}>
            <div style={{
              height: "100%",
              width: `${step.progress || 0}%`,
              background: getProgressColor(),
              borderRadius: "3px",
              transition: "width 0.3s"
            }} />
          </div>

          <div style={{ 
            fontSize: "0.85rem", 
            color: "var(--text-muted)",
            display: "flex",
            justifyContent: "space-between"
          }}>
            <span>{step.progress || 0}% completo</span>
          </div>
        </div>

        {!step.locked && (
          <ChevronRight size={20} style={{ color: "var(--text-muted)", marginLeft: "12px" }} />
        )}
      </div>
    </div>
  );
}

// Componente de visão geral
function OverviewCard({ title, value, subtitle, icon: Icon, color }) {
  return (
    <div className="card" style={{ textAlign: "center" }}>
      <div style={{ 
        display: "flex", 
        alignItems: "center", 
        justifyContent: "center",
        gap: "8px",
        marginBottom: "8px"
      }}>
        <Icon size={18} style={{ color }} />
        <span className="card-title" style={{ margin: 0, fontSize: "0.85rem" }}>{title}</span>
      </div>
      <div style={{ fontSize: "2rem", fontWeight: 700, color }}>{value}</div>
      {subtitle && (
        <div className="card-subtitle" style={{ marginTop: "4px" }}>{subtitle}</div>
      )}
    </div>
  );
}

export default function FounderDashboard() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [trails, setTrails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    try {
      setLoading(true);
      setError(null);
      const data = await apiGet("/founder/trails");
      setTrails(data || []);
    } catch (err) {
      console.error("Erro ao carregar dashboard:", err);
      setError(err.message || "Erro ao carregar dashboard. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  // Calcular estatísticas gerais
  const stats = trails.reduce((acc, trail) => {
    const steps = trail.steps || [];
    acc.totalSteps += steps.length;
    acc.completedSteps += steps.filter(s => s.completed).length;
    acc.inProgressSteps += steps.filter(s => !s.locked && !s.completed && s.progress > 0).length;
    acc.lockedSteps += steps.filter(s => s.locked).length;
    acc.totalProgress += steps.reduce((sum, s) => sum + (s.progress || 0), 0);
    return acc;
  }, { totalSteps: 0, completedSteps: 0, inProgressSteps: 0, lockedSteps: 0, totalProgress: 0 });

  const overallProgress = stats.totalSteps > 0 
    ? Math.round(stats.totalProgress / stats.totalSteps) 
    : 0;

  if (loading) {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <RefreshCw size={32} style={{ color: "var(--primary)", animation: "spin 1s linear infinite" }} />
        <p style={{ marginTop: "16px", color: "var(--text-muted)" }}>Carregando dashboard...</p>
        <style jsx>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <p style={{ color: "#ef4444", marginBottom: "16px" }}>Erro: {error}</p>
        <button onClick={loadDashboardData} className="btn btn-primary">
          Tentar novamente
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header com info do usuário */}
      <div style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center", 
        marginBottom: "24px",
        padding: "16px 20px",
        background: "var(--card-bg)",
        borderRadius: "12px",
        border: "1px solid var(--border)"
      }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{
              width: "40px",
              height: "40px",
              borderRadius: "50%",
              background: "var(--primary)",
              color: "white",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: "600",
              fontSize: "1rem"
            }}>
              {user?.name?.charAt(0)?.toUpperCase() || "F"}
            </div>
            <div>
              <div style={{ fontWeight: "600", color: "var(--text)" }}>
                {user?.name || "Founder"}
              </div>
              <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                {user?.company_name || user?.email}
              </div>
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button 
            onClick={loadDashboardData} 
            className="btn btn-ghost"
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <RefreshCw size={16} />
            Atualizar
          </button>
          <button 
            onClick={logout} 
            className="btn btn-ghost"
            style={{ display: "flex", alignItems: "center", gap: "6px", color: "#ef4444" }}
          >
            <LogOut size={16} />
            Sair
          </button>
        </div>
      </div>

      <div style={{ marginBottom: "24px" }}>
        <h1 style={{ margin: 0 }}>Seu Painel de Progresso</h1>
        <p style={{ color: "var(--text-muted)", marginTop: "8px" }}>
          Acompanhe sua evolução em cada trilha e etapa
        </p>
      </div>

      {/* Cards de visão geral */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
        gap: "16px",
        marginBottom: "32px"
      }}>
        <OverviewCard 
          title="Progresso Geral" 
          value={`${overallProgress}%`} 
          icon={TrendingUp}
          color="var(--primary)"
        />
        <OverviewCard 
          title="Concluídas" 
          value={stats.completedSteps} 
          subtitle={`de ${stats.totalSteps} etapas`}
          icon={CheckCircle}
          color="#10b981"
        />
        <OverviewCard 
          title="Em Andamento" 
          value={stats.inProgressSteps} 
          subtitle="etapas ativas"
          icon={Clock}
          color="#f59e0b"
        />
        <OverviewCard 
          title="Bloqueadas" 
          value={stats.lockedSteps} 
          subtitle="aguardando"
          icon={Lock}
          color="#94a3b8"
        />
      </div>

      {/* Trilhas e etapas */}
      {trails.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "40px" }}>
          <BarChart3 size={48} style={{ color: "var(--text-muted)", marginBottom: "16px" }} />
          <h3>Nenhuma trilha disponível</h3>
          <p style={{ color: "var(--text-muted)" }}>
            Entre em contato com o administrador para ter acesso às trilhas.
          </p>
        </div>
      ) : (
        trails.map((trail) => {
          const trailSteps = trail.steps || [];
          const trailProgress = trailSteps.length > 0
            ? Math.round(trailSteps.reduce((sum, s) => sum + (s.progress || 0), 0) / trailSteps.length)
            : 0;
          const completedCount = trailSteps.filter(s => s.completed).length;

          return (
            <div key={trail.id} style={{ marginBottom: "32px" }}>
              {/* Header da trilha */}
              <div style={{ 
                display: "flex", 
                justifyContent: "space-between", 
                alignItems: "center",
                marginBottom: "16px"
              }}>
                <div>
                  <h2 style={{ margin: 0 }}>{trail.name}</h2>
                  {trail.description && (
                    <p style={{ color: "var(--text-muted)", margin: "4px 0 0", fontSize: "0.9rem" }}>
                      {trail.description}
                    </p>
                  )}
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ 
                    fontSize: "1.5rem", 
                    fontWeight: 700, 
                    color: "var(--primary)" 
                  }}>
                    {trailProgress}%
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    {completedCount}/{trailSteps.length} etapas
                  </div>
                </div>
              </div>

              {/* Barra de progresso da trilha */}
              <div style={{
                height: "8px",
                background: "#e5e7eb",
                borderRadius: "4px",
                overflow: "hidden",
                marginBottom: "20px"
              }}>
                <div style={{
                  height: "100%",
                  width: `${trailProgress}%`,
                  background: trailProgress >= 100 ? "#10b981" : "var(--primary)",
                  borderRadius: "4px",
                  transition: "width 0.3s"
                }} />
              </div>

              {/* Grid de etapas */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
                gap: "16px"
              }}>
                {trailSteps.map((step) => (
                  <StepCard
                    key={step.id}
                    step={step}
                    trailId={trail.id}
                    onClick={() => router.push(`/founder/templates/${trail.id}/${step.id}`)}
                  />
                ))}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
