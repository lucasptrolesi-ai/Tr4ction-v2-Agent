"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useState, useEffect } from "react";

export default function TrailDetailPage() {
  const params = useParams();
  const router = useRouter();
  const trailId = params.trailId;

  const [trail, setTrail] = useState({
    id: trailId,
    name: "Trilha de Marketing",
    description: "Trilha completa de ICP, Persona, SWOT e estratégias",
    steps: [
      { id: "icp", name: "ICP - Ideal Customer Profile", order: 1 },
      { id: "persona", name: "Persona", order: 2 },
      { id: "swot", name: "Análise SWOT", order: 3 },
      { id: "funil", name: "Funil de Marketing", order: 4 }
    ]
  });

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
        <h1 style={{ margin: 0 }}>{trail.name}</h1>
      </div>

      <p style={{ color: "var(--text-muted)", maxWidth: 620, marginBottom: 32 }}>
        {trail.description}
      </p>

      <div style={{ display: "flex", gap: 16, marginBottom: 32 }}>
        <Link href={`/admin/trails/${trailId}/upload`}>
          <button className="btn btn-primary">
            📤 Upload Excel com Schema
          </button>
        </Link>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Etapas da Trilha</h2>
        
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {trail.steps.map((step) => (
            <Link 
              key={step.id} 
              href={`/admin/trails/${trailId}/steps/${step.id}`}
              style={{ textDecoration: "none" }}
            >
              <div 
                className="card"
                style={{ 
                  cursor: "pointer",
                  transition: "all 0.2s",
                  border: "1px solid var(--border)"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>
                      {step.order}. {step.name}
                    </div>
                    <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                      Clique para revisar schema
                    </div>
                  </div>
                  <div style={{ fontSize: "1.5rem" }}>→</div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
