"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import axios from "axios";
import { Download } from "lucide-react";

export default function UserTrailProgressPage() {
  const params = useParams();
  const router = useRouter();
  const { userId, trailId } = params;
  const backendBase = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

  const [user, setUser] = useState(null);
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProgress();
  }, [userId, trailId]);

  async function loadProgress() {
    try {
      setLoading(true);
      const res = await axios.get(`${backendBase}/admin/users/${userId}/trail/${trailId}/progress`);
      setUser(res.data.user);
      setProgress(res.data.steps);
    } catch (err) {
      console.error("Erro ao carregar progresso:", err);
      // Mock data
      setUser({ id: userId, name: "Founder Mock", email: "founder@example.com" });
      setProgress([
        { id: "icp", name: "ICP", locked: false, completed: true, progress: 100 },
        { id: "persona", name: "Persona", locked: false, completed: false, progress: 60 },
        { id: "swot", name: "SWOT", locked: true, completed: false, progress: 0 },
        { id: "funil", name: "Funil", locked: true, completed: false, progress: 0 }
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function toggleLock(stepId, currentlyLocked) {
    try {
      await axios.post(`${backendBase}/admin/users/${userId}/trail/${trailId}/steps/${stepId}/lock`, {
        locked: !currentlyLocked
      });
      await loadProgress();
    } catch (err) {
      console.error("Erro ao alterar lock:", err);
      alert("Erro ao alterar status: " + (err.response?.data?.detail || err.message));
    }
  }

  function handleDownloadXLSX() {
    window.open(`${backendBase}/admin/users/${userId}/trails/${trailId}/export/xlsx`, "_blank");
  }

  if (loading) {
    return <div><h1>Carregando...</h1></div>;
  }

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", alignItems: "center", gap: 12 }}>
        <button 
          onClick={() => router.back()} 
          className="btn btn-ghost"
          style={{ padding: "8px 16px" }}
        >
          ← Voltar
        </button>
        <h1 style={{ margin: 0 }}>Progresso de {user?.name || userId}</h1>
        <button
          onClick={handleDownloadXLSX}
          className="btn"
          style={{ 
            marginLeft: "auto",
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

      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginTop: 0 }}>Informações do Usuário</h3>
        <div style={{ fontSize: "0.9rem" }}>
          <div style={{ marginBottom: 8 }}><strong>ID:</strong> {user?.id}</div>
          <div style={{ marginBottom: 8 }}><strong>Nome:</strong> {user?.name}</div>
          <div><strong>Email:</strong> {user?.email}</div>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Trilha: {trailId}</h3>
        
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {progress.map((step) => (
            <div 
              key={step.id}
              className="card"
              style={{
                border: "1px solid var(--border)",
                background: step.locked ? "#f5f5f5" : "#fff"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>
                    {step.locked && "🔒 "}
                    {step.completed && "✅ "}
                    {step.name}
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    Progresso: {step.progress}%
                  </div>
                  <div style={{ 
                    marginTop: 8,
                    height: 6,
                    background: "#eee",
                    borderRadius: 3,
                    overflow: "hidden"
                  }}>
                    <div style={{
                      height: "100%",
                      width: `${step.progress}%`,
                      background: step.completed ? "#4caf50" : "var(--primary)",
                      transition: "width 0.3s"
                    }} />
                  </div>
                </div>
                
                <button
                  onClick={() => toggleLock(step.id, step.locked)}
                  className="btn btn-ghost"
                  style={{ marginLeft: 16 }}
                >
                  {step.locked ? "🔓 Desbloquear" : "🔒 Bloquear"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
