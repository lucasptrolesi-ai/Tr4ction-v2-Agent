"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { 
  Users, ChevronDown, ChevronUp, Download, Unlock, Eye, 
  FileSpreadsheet, CheckCircle, AlertTriangle, RefreshCw,
  Search, Filter
} from "lucide-react";
import { apiGet, apiPost } from "@/lib/api";

function FounderCard({ founder, onUnlock, onDownload, onViewAnswers }) {
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
        Risco {style.label}
      </span>
    );
  };

  return (
    <div className="card" style={{ marginBottom: "16px" }}>
      {/* Header do card */}
      <div 
        style={{ 
          display: "flex", 
          justifyContent: "space-between", 
          alignItems: "center",
          cursor: "pointer"
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "40px",
            height: "40px",
            borderRadius: "50%",
            background: "var(--primary)",
            color: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 600
          }}>
            {founder.name.charAt(0)}
          </div>
          <div>
            <div style={{ fontWeight: 600 }}>{founder.name}</div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>{founder.email}</div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {getRiskBadge(founder.risk)}
          
          {/* Progresso */}
          <div style={{ textAlign: "right", minWidth: "80px" }}>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--primary)" }}>
              {founder.progress}%
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>progresso</div>
          </div>

          {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </div>
      </div>

      {/* Conteúdo expandido */}
      {expanded && (
        <div style={{ marginTop: "20px", paddingTop: "20px", borderTop: "1px solid var(--border)" }}>
          {/* Etapa atual */}
          <div style={{ marginBottom: "16px" }}>
            <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Etapa atual: </span>
            <span style={{ fontWeight: 500 }}>{founder.currentStep}</span>
          </div>

          {/* Steps */}
          <div style={{ marginBottom: "20px" }}>
            <h4 style={{ fontSize: "0.9rem", marginBottom: "12px" }}>Progresso por Etapa</h4>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "12px" }}>
              {founder.steps?.map((step) => (
                <div
                  key={step.id}
                  style={{
                    padding: "12px 16px",
                    background: step.locked ? "#f1f5f9" : "#fff",
                    border: `1px solid ${step.completed ? "#10b981" : "var(--border)"}`,
                    borderRadius: "8px",
                    minWidth: "200px",
                    opacity: step.locked ? 0.7 : 1
                  }}
                >
                  <div style={{ 
                    display: "flex", 
                    justifyContent: "space-between", 
                    alignItems: "center",
                    marginBottom: "8px"
                  }}>
                    <span style={{ fontWeight: 500, fontSize: "0.85rem" }}>
                      {step.name}
                    </span>
                    {step.completed && <CheckCircle size={16} style={{ color: "#10b981" }} />}
                    {step.locked && (
                      <button
                        className="btn btn-ghost"
                        style={{ padding: "4px 8px", fontSize: "0.7rem" }}
                        onClick={(e) => { e.stopPropagation(); onUnlock(founder.id, step.id); }}
                      >
                        <Unlock size={12} style={{ marginRight: "4px" }} />
                        Desbloquear
                      </button>
                    )}
                  </div>
                  
                  {/* Barra de progresso */}
                  <div style={{
                    height: "4px",
                    background: "#e5e7eb",
                    borderRadius: "2px",
                    overflow: "hidden"
                  }}>
                    <div style={{
                      height: "100%",
                      width: `${step.progress || 0}%`,
                      background: step.completed ? "#10b981" : "var(--primary)",
                      borderRadius: "2px"
                    }} />
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>
                    {step.progress || 0}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Ações */}
          <div style={{ display: "flex", gap: "12px" }}>
            <button
              className="btn btn-secondary"
              onClick={() => onViewAnswers(founder)}
              style={{ display: "flex", alignItems: "center", gap: "6px" }}
            >
              <Eye size={16} />
              Ver Respostas
            </button>
            <button
              className="btn btn-primary"
              onClick={() => onDownload(founder)}
              style={{ display: "flex", alignItems: "center", gap: "6px" }}
            >
              <Download size={16} />
              Baixar XLSX
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AdminFounders() {
  const router = useRouter();
  const [founders, setFounders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");

  useEffect(() => {
    loadFounders();
  }, []);

  async function loadFounders() {
    try {
      setLoading(true);
      const data = await apiGet("/admin/founders/progress");
      setFounders(data || []);
    } catch (err) {
      console.error("Erro ao carregar founders:", err);
      // Fallback para mock
      setFounders(getMockFounders());
    } finally {
      setLoading(false);
    }
  }

  function getMockFounders() {
    return [
      {
        id: "demo-user",
        name: "Demo Founder",
        email: "demo@tr4ction.com",
        currentStep: "ICP",
        progress: 45,
        risk: "low",
        trailId: "test-trilha",
        steps: [
          { id: "icp", name: "ICP", progress: 80, completed: false, locked: false },
          { id: "persona", name: "Persona", progress: 40, completed: false, locked: false },
          { id: "swot", name: "SWOT", progress: 0, completed: false, locked: true }
        ]
      }
    ];
  }

  async function handleUnlock(founderId, stepId) {
    try {
      await apiPost(`/admin/founders/${founderId}/steps/${stepId}/unlock`, {});
      alert(`Etapa ${stepId} desbloqueada!`);
      loadFounders();
    } catch (err) {
      alert("Erro ao desbloquear: " + err.message);
    }
  }

  function handleDownload(founder) {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
    window.open(`${apiBase}/founder/trails/${founder.trailId}/export/xlsx?user_id=${founder.id}`, "_blank");
  }

  function handleViewAnswers(founder) {
    router.push(`/admin/founders/${founder.id}/answers?trail=${founder.trailId}`);
  }

  // Filtros
  const filteredFounders = founders.filter(f => {
    const matchesSearch = f.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          f.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRisk = riskFilter === "all" || f.risk === riskFilter;
    return matchesSearch && matchesRisk;
  });

  if (loading) {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <RefreshCw size={32} style={{ color: "var(--primary)", animation: "spin 1s linear infinite" }} />
        <p style={{ marginTop: "16px", color: "var(--text-muted)" }}>Carregando founders...</p>
        <style jsx>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 style={{ margin: 0 }}>
            <Users size={28} style={{ marginRight: "12px", verticalAlign: "middle" }} />
            Founders & Startups
          </h1>
          <p style={{ color: "var(--text-muted)", marginTop: "8px" }}>
            Gerencie o progresso e acesso de cada founder
          </p>
        </div>
        <button 
          onClick={loadFounders} 
          className="btn btn-secondary"
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <RefreshCw size={16} />
          Atualizar
        </button>
      </div>

      {/* Filtros */}
      <div className="card" style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
          {/* Busca */}
          <div style={{ flex: 1, minWidth: "200px", position: "relative" }}>
            <Search size={18} style={{ 
              position: "absolute", 
              left: "12px", 
              top: "50%", 
              transform: "translateY(-50%)",
              color: "var(--text-muted)"
            }} />
            <input
              type="text"
              placeholder="Buscar por nome ou email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 12px 10px 40px",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                fontSize: "0.9rem"
              }}
            />
          </div>

          {/* Filtro de risco */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Filter size={18} style={{ color: "var(--text-muted)" }} />
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              style={{
                padding: "10px 12px",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                fontSize: "0.9rem",
                background: "#fff"
              }}
            >
              <option value="all">Todos os riscos</option>
              <option value="high">Alto risco</option>
              <option value="medium">Médio risco</option>
              <option value="low">Baixo risco</option>
            </select>
          </div>
        </div>
      </div>

      {/* Lista de founders */}
      {filteredFounders.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "40px" }}>
          <Users size={48} style={{ color: "var(--text-muted)", marginBottom: "16px" }} />
          <h3>Nenhum founder encontrado</h3>
          <p style={{ color: "var(--text-muted)" }}>
            {searchTerm || riskFilter !== "all" 
              ? "Tente ajustar os filtros de busca."
              : "Aguardando founders iniciarem suas trilhas."}
          </p>
        </div>
      ) : (
        filteredFounders.map((founder) => (
          <FounderCard
            key={founder.id}
            founder={founder}
            onUnlock={handleUnlock}
            onDownload={handleDownload}
            onViewAnswers={handleViewAnswers}
          />
        ))
      )}

      {/* Resumo */}
      {filteredFounders.length > 0 && (
        <div style={{ 
          marginTop: "24px", 
          padding: "16px", 
          background: "#f8fafc", 
          borderRadius: "8px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}>
          <span style={{ color: "var(--text-muted)" }}>
            Mostrando {filteredFounders.length} de {founders.length} founders
          </span>
          <button
            className="btn btn-ghost"
            onClick={() => {
              const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
              window.open(`${apiBase}/admin/founders/export/xlsx`, "_blank");
            }}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <FileSpreadsheet size={16} />
            Exportar Todos
          </button>
        </div>
      )}
    </div>
  );
}
