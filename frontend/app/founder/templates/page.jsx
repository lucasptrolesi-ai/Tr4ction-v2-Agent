"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Lock, CheckCircle, Clock, Download, WifiOff, RefreshCw } from "lucide-react";
import { apiGet, apiDownload } from "@/lib/api";

export default function TemplatesPage() {
  const router = useRouter();
  const [trails, setTrails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Mock para fallback quando offline
  const mockTrails = [
    {
      id: "q1-marketing",
      name: "Marketing Q1 (offline)",
      description: "Template completo de marketing para o primeiro trimestre",
      steps: [
        { id: "icp", name: "ICP", locked: false, completed: true, progress: 100 },
        { id: "persona", name: "Persona", locked: false, completed: false, progress: 60 },
        { id: "swot", name: "SWOT", locked: false, completed: false, progress: 30 },
        { id: "funil", name: "Funil de Vendas", locked: true, completed: false, progress: 0 },
        { id: "metricas", name: "Métricas", locked: true, completed: false, progress: 0 }
      ]
    }
  ];

  useEffect(() => {
    loadTrails();
  }, []);

  async function loadTrails() {
    try {
      setLoading(true);
      setOffline(false);
      setErrorMsg(null);
      
      const data = await apiGet("/founder/trails");
      setTrails(data);
    } catch (err) {
      console.error("Erro ao carregar trilhas:", err);
      setOffline(true);
      setErrorMsg("Não foi possível conectar ao backend. Exibindo dados demonstrativos.");
      setTrails(mockTrails);
    } finally {
      setLoading(false);
    }
  }

  async function handleDownloadTrail(trailId) {
    try {
      if (offline) {
        alert("Download disponível quando o backend estiver ativo.");
        return;
      }
      // Usa o novo endpoint de export XLSX
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
      window.open(`${apiBase}/founder/trails/${trailId}/export/xlsx`, "_blank");
    } catch (err) {
      console.error("Erro ao baixar:", err);
      alert("Erro ao baixar template: " + err.message);
    }
  }

  function getStepIcon(step) {
    if (step.locked) {
      return <Lock size={20} style={{ color: "#94a3b8" }} />;
    }
    if (step.completed) {
      return <CheckCircle size={20} style={{ color: "#10b981" }} />;
    }
    return <Clock size={20} style={{ color: "#f59e0b" }} />;
  }

  function getProgressColor(progress) {
    if (progress === 100) return "#10b981";
    if (progress >= 50) return "#f59e0b";
    if (progress > 0) return "#3b82f6";
    return "#e5e7eb";
  }

  if (loading) {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <div style={{ fontSize: "1.2rem", color: "var(--text-muted)" }}>
          Carregando trilhas...
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Banner de Offline com botão Tentar Novamente */}
      {offline && (
        <div 
          className="card" 
          style={{ 
            marginBottom: "16px", 
            display: "flex", 
            alignItems: "center", 
            justifyContent: "space-between",
            gap: "12px", 
            background: "#fff7ed", 
            borderColor: "#fdba74" 
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <WifiOff size={20} style={{ color: "#ea580c" }} />
            <div style={{ color: "#9a3412", fontSize: "0.9rem" }}>
              Backend offline: exibindo dados mock para navegação.
            </div>
          </div>
          <button 
            onClick={loadTrails}
            className="btn btn-ghost"
            style={{ padding: "6px 12px", display: "flex", alignItems: "center", gap: "6px" }}
          >
            <RefreshCw size={16} />
            Tentar novamente
          </button>
        </div>
      )}

      <div style={{ marginBottom: "32px" }}>
        <h1>📋 Meus Templates</h1>
        <p style={{ color: "var(--text-muted)", maxWidth: 620 }}>
          Preencha os templates etapa por etapa. Use o chat lateral para tirar dúvidas 
          e receber orientações do agente de marketing.
        </p>
        {errorMsg && !offline && (
          <p style={{ color: "#b45309", fontSize: "0.85rem", marginTop: "8px" }}>{errorMsg}</p>
        )}
      </div>

      {trails.map((trail) => (
        <div key={trail.id} className="card" style={{ marginBottom: "24px" }}>
          <div style={{ 
            display: "flex", 
            justifyContent: "space-between", 
            alignItems: "flex-start",
            marginBottom: "20px" 
          }}>
            <div>
              <h2 style={{ margin: 0, marginBottom: "8px" }}>{trail.name}</h2>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", margin: 0 }}>
                {trail.description}
              </p>
            </div>
            
            <button
              onClick={() => handleDownloadTrail(trail.id)}
              className="btn"
              style={{ 
                display: "flex", 
                alignItems: "center", 
                gap: "8px",
                background: "#16a34a",
                color: "white",
                border: "none"
              }}
            >
              <Download size={16} />
              Baixar XLSX
            </button>
          </div>

          <div style={{ 
            display: "grid", 
            gap: "12px",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))"
          }}>
            {trail.steps.map((step) => (
              <div
                key={step.id}
                onClick={() => !step.locked && router.push(`/founder/templates/${trail.id}/${step.id}`)}
                style={{
                  padding: "16px",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  cursor: step.locked ? "not-allowed" : "pointer",
                  background: step.locked ? "#f9fafb" : "#fff",
                  opacity: step.locked ? 0.6 : 1,
                  transition: "all 0.2s",
                  position: "relative"
                }}
                onMouseEnter={(e) => {
                  if (!step.locked) e.currentTarget.style.borderColor = "var(--primary)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border)";
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    {getStepIcon(step)}
                    <span style={{ fontWeight: 600 }}>{step.name}</span>
                  </div>
                  
                  <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    {step.progress}%
                  </span>
                </div>

                {/* Barra de progresso */}
                <div style={{
                  width: "100%",
                  height: "6px",
                  background: "#e5e7eb",
                  borderRadius: "3px",
                  overflow: "hidden"
                }}>
                  <div style={{
                    width: `${step.progress}%`,
                    height: "100%",
                    background: getProgressColor(step.progress),
                    transition: "width 0.3s"
                  }} />
                </div>

                {step.locked && (
                  <div style={{ 
                    fontSize: "0.8rem", 
                    color: "#64748b", 
                    marginTop: "8px",
                    fontStyle: "italic"
                  }}>
                    🔒 Aguardando liberação
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
