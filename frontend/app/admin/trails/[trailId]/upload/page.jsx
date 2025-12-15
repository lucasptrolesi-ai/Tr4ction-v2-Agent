"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle, ArrowLeft } from "lucide-react";

export default function TrailUploadPage() {
  const params = useParams();
  const router = useRouter();
  const trailId = params.trailId;
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  function handleFileChange(e) {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setResult(null);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && (droppedFile.name.endsWith('.xlsx') || droppedFile.name.endsWith('.xls'))) {
      setFile(droppedFile);
      setError(null);
      setResult(null);
    } else {
      setError("Por favor, selecione um arquivo Excel (.xlsx ou .xls)");
    }
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) {
      setError("Selecione um arquivo Excel");
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${apiBase}/admin/trails/${trailId}/upload-xlsx?replace_existing=true`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Erro ao processar arquivo");
      }

      setResult(data);
      setFile(null);
    } catch (err) {
      console.error("Erro no upload:", err);
      setError(err.message || "Erro ao processar arquivo");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", alignItems: "center", gap: 12 }}>
        <button 
          onClick={() => router.back()} 
          className="btn btn-ghost"
          style={{ padding: "8px 16px", display: "flex", alignItems: "center", gap: 6 }}
        >
          <ArrowLeft size={16} />
          Voltar
        </button>
        <h1 style={{ margin: 0 }}>Upload de Template - {trailId}</h1>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <h2 style={{ marginTop: 0, display: "flex", alignItems: "center", gap: 8 }}>
          <FileSpreadsheet size={24} />
          Formato do Excel
        </h2>
        <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginBottom: 16 }}>
          O sistema irá ler automaticamente cada <strong>aba</strong> como uma etapa da trilha.
        </p>
        <div style={{ 
          background: "#f8f9fa", 
          padding: 16, 
          borderRadius: 8,
          fontSize: "0.9rem",
          lineHeight: 1.8
        }}>
          <div><strong>Estrutura esperada:</strong></div>
          <ul style={{ marginTop: 8, paddingLeft: 20 }}>
            <li>Cada <strong>aba</strong> = uma etapa (ICP, Persona, SWOT, etc.)</li>
            <li><strong>Coluna A</strong> = Label do campo (nome que aparece no formulário)</li>
            <li><strong>Coluna B</strong> = Valor exemplo ou placeholder (opcional)</li>
          </ul>
          <div style={{ marginTop: 12, padding: 12, background: "#fff", borderRadius: 4, fontFamily: "monospace", fontSize: "0.8rem" }}>
            <div>📋 <strong>Aba "ICP":</strong></div>
            <div style={{ marginLeft: 20 }}>A1: Segmento de Mercado | B1: Ex: SaaS B2B</div>
            <div style={{ marginLeft: 20 }}>A2: Porte da Empresa | B2: Ex: PME 10-50 funcionários</div>
            <div style={{ marginLeft: 20 }}>A3: Região de Atuação | B3: Ex: Brasil, LATAM</div>
          </div>
        </div>
      </div>

      <form onSubmit={handleUpload}>
        <div 
          className="card"
          style={{ 
            border: dragOver ? "2px dashed var(--primary)" : "2px dashed var(--border)",
            background: dragOver ? "#f0f7ff" : "transparent",
            transition: "all 0.2s"
          }}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <div style={{ textAlign: "center", padding: "40px 20px" }}>
            <Upload size={48} style={{ color: "var(--text-muted)", marginBottom: 16 }} />
            <div style={{ fontSize: "1.1rem", marginBottom: 8 }}>
              Arraste o arquivo Excel aqui
            </div>
            <div style={{ color: "var(--text-muted)", marginBottom: 16 }}>
              ou clique para selecionar
            </div>
            
            <input
              type="file"
              id="file-input"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
              disabled={uploading}
              style={{ display: "none" }}
            />
            <label 
              htmlFor="file-input"
              className="btn btn-secondary"
              style={{ cursor: "pointer" }}
            >
              Selecionar Arquivo
            </label>
          </div>

          {file && (
            <div style={{ 
              borderTop: "1px solid var(--border)", 
              padding: "16px 20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <FileSpreadsheet size={24} style={{ color: "#16a34a" }} />
                <div>
                  <div style={{ fontWeight: 600 }}>{file.name}</div>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    {(file.size / 1024).toFixed(2)} KB
                  </div>
                </div>
              </div>
              
              <button 
                type="submit" 
                className="btn"
                disabled={uploading}
                style={{ 
                  background: "#16a34a", 
                  color: "white",
                  display: "flex",
                  alignItems: "center",
                  gap: 8
                }}
              >
                <Upload size={16} />
                {uploading ? "Processando..." : "Enviar e Processar"}
              </button>
            </div>
          )}
        </div>
      </form>

      {error && (
        <div className="card" style={{ marginTop: 24, background: "#fef2f2", borderColor: "#fca5a5" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, color: "#dc2626" }}>
            <AlertCircle size={24} />
            <div>
              <div style={{ fontWeight: 600 }}>Erro no Upload</div>
              <div style={{ fontSize: "0.9rem", marginTop: 4 }}>{error}</div>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div className="card" style={{ marginTop: 24, background: "#f0fdf4", borderColor: "#86efac" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
            <CheckCircle size={24} style={{ color: "#16a34a", flexShrink: 0, marginTop: 2 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, color: "#166534", marginBottom: 12 }}>
                Template Processado com Sucesso!
              </div>
              
              <div style={{ 
                background: "white", 
                padding: 16, 
                borderRadius: 8,
                fontSize: "0.9rem"
              }}>
                <div style={{ marginBottom: 12 }}>
                  <strong>Trilha:</strong> {result.data?.trail_id}
                </div>
                <div style={{ marginBottom: 12 }}>
                  <strong>Arquivo:</strong> {result.data?.file_name}
                </div>
                <div style={{ marginBottom: 12 }}>
                  <strong>Etapas criadas:</strong> {result.data?.steps_created}
                </div>
                
                {result.data?.steps && (
                  <div>
                    <strong>Detalhes:</strong>
                    <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                      {result.data.steps.map((step, idx) => (
                        <li key={idx}>
                          <strong>{step.step_name}</strong> - {step.fields_count} campos
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div style={{ marginTop: 16, display: "flex", gap: 12 }}>
                <button 
                  onClick={() => router.push(`/admin/trails/${trailId}`)}
                  className="btn btn-primary"
                >
                  Ver Trilha
                </button>
                <button 
                  onClick={() => router.push(`/founder/templates`)}
                  className="btn btn-secondary"
                >
                  Testar como Founder
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
