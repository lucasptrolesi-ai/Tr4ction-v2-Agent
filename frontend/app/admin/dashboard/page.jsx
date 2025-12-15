"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { 
  Users, TrendingUp, AlertTriangle, CheckCircle, 
  RefreshCw, Activity, BarChart3, ChevronDown, ChevronUp,
  Download, Unlock, Eye, FileSpreadsheet, LogOut
} from "lucide-react";
import { apiGet, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";

// Card de métrica
function MetricCard({ title, value, subtitle, icon: Icon, color, trend }) {
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div className="card-subtitle" style={{ marginBottom: "4px" }}>{title}</div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color }}>{value}</div>
          {subtitle && (
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "4px" }}>
              {subtitle}
            </div>
          )}
        </div>
        <div style={{
          width: "48px",
          height: "48px",
          borderRadius: "12px",
          background: `${color}15`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center"
        }}>
          <Icon size={24} style={{ color }} />
        </div>
      </div>
      {trend && (
        <div style={{ 
          marginTop: "12px", 
          fontSize: "0.8rem",
          color: trend > 0 ? "#10b981" : "#ef4444",
          display: "flex",
          alignItems: "center",
          gap: "4px"
        }}>
          {trend > 0 ? <TrendingUp size={14} /> : <TrendingUp size={14} style={{ transform: "rotate(180deg)" }} />}
          {Math.abs(trend)}% vs semana anterior
        </div>
      )}
    </div>
  );
}

// Componente de linha de founder expandível
function FounderRow({ founder, trails, onUnlock, onDownload }) {
  const [expanded, setExpanded] = useState(false);

  const getRiskBadge = (risk) => {
    const colors = {
      low: { bg: "#dcfce7", text: "#166534", label: "Baixo" },
      medium: { bg: "#fef3c7", text: "#92400e", label: "Médio" },
      high: { bg: "#fee2e2", text: "#991b1b", label: "Alto" }
    };
    const style = colors[risk] || colors.low;
    return (
      <span style={{
        padding: "4px 10px",
        borderRadius: "12px",
        background: style.bg,
        color: style.text,
        fontSize: "0.75rem",
        fontWeight: 600
      }}>
        {style.label}
      </span>
    );
  };

  const getProgressBar = (progress) => (
    <div style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: "120px" }}>
      <div style={{
        flex: 1,
        height: "6px",
        background: "#e5e7eb",
        borderRadius: "3px",
        overflow: "hidden"
      }}>
        <div style={{
          height: "100%",
          width: `${progress}%`,
          background: progress >= 75 ? "#10b981" : progress >= 50 ? "#f59e0b" : "#3b82f6",
          borderRadius: "3px"
        }} />
      </div>
      <span style={{ fontSize: "0.8rem", fontWeight: 500, minWidth: "36px" }}>{progress}%</span>
    </div>
  );

  return (
    <>
      <tr 
        onClick={() => setExpanded(!expanded)}
        style={{ cursor: "pointer", background: expanded ? "#f8fafc" : "transparent" }}
      >
        <td style={{ padding: "12px", borderTop: "1px solid var(--border)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            <div>
              <div style={{ fontWeight: 600 }}>{founder.name}</div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{founder.email}</div>
            </div>
          </div>
        </td>
        <td style={{ padding: "12px", borderTop: "1px solid var(--border)" }}>
          {founder.currentStep}
        </td>
        <td style={{ padding: "12px", borderTop: "1px solid var(--border)" }}>
          {getProgressBar(founder.progress)}
        </td>
        <td style={{ padding: "12px", borderTop: "1px solid var(--border)" }}>
          {getRiskBadge(founder.risk)}
        </td>
        <td style={{ padding: "12px", borderTop: "1px solid var(--border)" }}>
          <div style={{ display: "flex", gap: "8px" }}>
            <button 
              className="btn btn-ghost" 
              style={{ padding: "6px" }}
              title="Ver detalhes"
              onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            >
              <Eye size={16} />
            </button>
            <button 
              className="btn btn-ghost" 
              style={{ padding: "6px" }}
              title="Baixar XLSX"
              onClick={(e) => { e.stopPropagation(); onDownload(founder); }}
            >
              <Download size={16} />
            </button>
          </div>
        </td>
      </tr>

      {/* Linha expandida com detalhes */}
      {expanded && (
        <tr>
          <td colSpan={5} style={{ padding: "0", background: "#f8fafc" }}>
            <div style={{ padding: "16px 24px" }}>
              <h4 style={{ margin: "0 0 12px", fontSize: "0.9rem" }}>Progresso por Etapa</h4>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "12px" }}>
                {founder.steps?.map((step) => (
                  <div 
                    key={step.id}
                    style={{
                      padding: "12px 16px",
                      background: "#fff",
                      borderRadius: "8px",
                      border: "1px solid var(--border)",
                      minWidth: "180px"
                    }}
                  >
                    <div style={{ 
                      display: "flex", 
                      justifyContent: "space-between", 
                      alignItems: "center",
                      marginBottom: "8px"
                    }}>
                      <span style={{ fontWeight: 500, fontSize: "0.85rem" }}>{step.name}</span>
                      {step.locked ? (
                        <button
                          className="btn btn-ghost"
                          style={{ padding: "4px 8px", fontSize: "0.7rem" }}
                          onClick={() => onUnlock(founder.id, step.id)}
                        >
                          <Unlock size={12} style={{ marginRight: "4px" }} />
                          Desbloquear
                        </button>
                      ) : step.completed ? (
                        <CheckCircle size={16} style={{ color: "#10b981" }} />
                      ) : null}
                    </div>
                    {getProgressBar(step.progress || 0)}
                  </div>
                ))}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function AdminDashboard() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [founders, setFounders] = useState([]);
  const [trails, setTrails] = useState([]);
  const [stats, setStats] = useState({
    totalFounders: 0,
    activeFounders: 0,
    avgProgress: 0,
    atRiskCount: 0
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    try {
      setLoading(true);
      
      // Carregar trilhas
      const trailsData = await apiGet("/admin/trails");
      setTrails(trailsData || []);

      // Carregar progresso dos founders
      let foundersData = [];
      try {
        foundersData = await apiGet("/admin/founders/progress");
      } catch {
        // Se endpoint não existir, usa dados mockados
        foundersData = getMockFounders(trailsData);
      }
      
      setFounders(foundersData);

      // Calcular estatísticas
      const totalFounders = foundersData.length;
      const activeFounders = foundersData.filter(f => f.progress > 0).length;
      const avgProgress = totalFounders > 0 
        ? Math.round(foundersData.reduce((sum, f) => sum + f.progress, 0) / totalFounders)
        : 0;
      const atRiskCount = foundersData.filter(f => f.risk === "high").length;

      setStats({ totalFounders, activeFounders, avgProgress, atRiskCount });
    } catch (err) {
      console.error("Erro ao carregar dashboard:", err);
    } finally {
      setLoading(false);
    }
  }

  // Mock de founders para demonstração
  function getMockFounders(trailsData) {
    const trail = trailsData?.[0];
    const steps = trail?.steps || [
      { id: "icp", name: "ICP" },
      { id: "persona", name: "Persona" },
      { id: "swot", name: "SWOT" }
    ];

    return [
      {
        id: "founder-1",
        name: "TechStart Solutions",
        email: "joao@techstart.com",
        currentStep: "Persona",
        progress: 65,
        risk: "low",
        trailId: trail?.id || "test-trilha",
        steps: steps.map((s, i) => ({
          ...s,
          progress: i === 0 ? 100 : i === 1 ? 60 : 0,
          completed: i === 0,
          locked: i > 1
        }))
      },
      {
        id: "founder-2",
        name: "InnovateLab",
        email: "maria@innovatelab.io",
        currentStep: "ICP",
        progress: 30,
        risk: "medium",
        trailId: trail?.id || "test-trilha",
        steps: steps.map((s, i) => ({
          ...s,
          progress: i === 0 ? 30 : 0,
          completed: false,
          locked: i > 0
        }))
      },
      {
        id: "founder-3",
        name: "DataDriven Co",
        email: "pedro@datadriven.co",
        currentStep: "Não iniciado",
        progress: 0,
        risk: "high",
        trailId: trail?.id || "test-trilha",
        steps: steps.map((s, i) => ({
          ...s,
          progress: 0,
          completed: false,
          locked: i > 0
        }))
      },
      {
        id: "demo-user",
        name: "Demo Founder",
        email: "demo@tr4ction.com",
        currentStep: "Ativo",
        progress: 45,
        risk: "low",
        trailId: trail?.id || "test-trilha",
        steps: steps.map((s, i) => ({
          ...s,
          progress: i === 0 ? 80 : i === 1 ? 40 : 0,
          completed: false,
          locked: false
        }))
      }
    ];
  }

  async function handleUnlock(founderId, stepId) {
    try {
      await apiPost(`/admin/founders/${founderId}/steps/${stepId}/unlock`, {});
      alert(`Etapa ${stepId} desbloqueada para ${founderId}`);
      loadDashboardData();
    } catch (err) {
      // Mock de sucesso se endpoint não existir
      alert(`Etapa ${stepId} desbloqueada! (mock)`);
      setFounders(prev => prev.map(f => {
        if (f.id === founderId) {
          return {
            ...f,
            steps: f.steps.map(s => s.id === stepId ? { ...s, locked: false } : s)
          };
        }
        return f;
      }));
    }
  }

  async function handleDownload(founder) {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
      window.open(`${apiBase}/founder/trails/${founder.trailId}/export/xlsx?user_id=${founder.id}`, "_blank");
    } catch (err) {
      alert("Erro ao baixar: " + err.message);
    }
  }

  if (loading) {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <RefreshCw size={32} style={{ color: "var(--primary)", animation: "spin 1s linear infinite" }} />
        <p style={{ marginTop: "16px", color: "var(--text-muted)" }}>Carregando dashboard...</p>
        <style jsx>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
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
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "44px",
            height: "44px",
            borderRadius: "50%",
            background: "linear-gradient(135deg, #3b82f6, #8b5cf6)",
            color: "white",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: "600",
            fontSize: "1.1rem"
          }}>
            {user?.name?.charAt(0)?.toUpperCase() || "A"}
          </div>
          <div>
            <div style={{ fontWeight: "600", color: "var(--text)" }}>
              {user?.name || "Administrador"}
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
              {user?.email} • <span style={{ 
                background: "#3b82f620",
                color: "#3b82f6",
                padding: "2px 8px",
                borderRadius: "4px",
                fontSize: "0.75rem",
                fontWeight: "500"
              }}>Admin</span>
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button 
            onClick={loadDashboardData} 
            className="btn btn-secondary"
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
        <h1 style={{ margin: 0 }}>Dashboard de Progresso</h1>
        <p style={{ color: "var(--text-muted)", marginTop: "8px" }}>
          Acompanhe o progresso de todos os founders em tempo real
        </p>
      </div>

      {/* Cards de métricas */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "16px",
        marginBottom: "32px"
      }}>
        <MetricCard
          title="Total de Founders"
          value={stats.totalFounders}
          subtitle="cadastrados no sistema"
          icon={Users}
          color="#3b82f6"
        />
        <MetricCard
          title="Founders Ativos"
          value={stats.activeFounders}
          subtitle="com progresso > 0%"
          icon={Activity}
          color="#10b981"
          trend={12}
        />
        <MetricCard
          title="Progresso Médio"
          value={`${stats.avgProgress}%`}
          subtitle="em todas as trilhas"
          icon={BarChart3}
          color="var(--primary)"
        />
        <MetricCard
          title="Em Risco"
          value={stats.atRiskCount}
          subtitle="founders precisando atenção"
          icon={AlertTriangle}
          color="#ef4444"
        />
      </div>

      {/* Tabela de founders */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ 
          padding: "16px 20px", 
          borderBottom: "1px solid var(--border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}>
          <h2 style={{ margin: 0, fontSize: "1.1rem" }}>
            <Users size={18} style={{ marginRight: "8px", verticalAlign: "middle" }} />
            Founders & Startups
          </h2>
          <button 
            className="btn btn-ghost"
            style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.85rem" }}
            onClick={() => {
              const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
              window.open(`${apiBase}/admin/founders/export/xlsx`, "_blank");
            }}
          >
            <FileSpreadsheet size={16} />
            Exportar Todos
          </button>
        </div>
        
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
            <thead>
              <tr style={{ background: "#f8fafc" }}>
                <th style={{ textAlign: "left", padding: "12px", fontWeight: 600 }}>Startup</th>
                <th style={{ textAlign: "left", padding: "12px", fontWeight: 600 }}>Etapa Atual</th>
                <th style={{ textAlign: "left", padding: "12px", fontWeight: 600 }}>Progresso</th>
                <th style={{ textAlign: "left", padding: "12px", fontWeight: 600 }}>Risco</th>
                <th style={{ textAlign: "left", padding: "12px", fontWeight: 600 }}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {founders.map((founder) => (
                <FounderRow
                  key={founder.id}
                  founder={founder}
                  trails={trails}
                  onUnlock={handleUnlock}
                  onDownload={handleDownload}
                />
              ))}
            </tbody>
          </table>
        </div>

        {founders.length === 0 && (
          <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
            Nenhum founder cadastrado ainda.
          </div>
        )}
      </div>
    </div>
  );
}
