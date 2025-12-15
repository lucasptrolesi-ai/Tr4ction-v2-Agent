"use client";

import { useState, useEffect, useCallback } from "react";
import axios from "axios";

// ======================================================
// Componente de Status Badge
// ======================================================
function StatusBadge({ status }) {
  const styles = {
    indexed: { bg: "#dcfce7", color: "#166534", label: "Indexado" },
    processing: { bg: "#fef3c7", color: "#92400e", label: "Processando..." },
    error: { bg: "#fee2e2", color: "#991b1b", label: "Erro" },
    pending: { bg: "#e0e7ff", color: "#3730a3", label: "Pendente" }
  };
  
  const style = styles[status] || styles.pending;
  
  return (
    <span style={{
      padding: "4px 8px",
      borderRadius: "4px",
      fontSize: "0.75rem",
      fontWeight: 500,
      backgroundColor: style.bg,
      color: style.color
    }}>
      {style.label}
    </span>
  );
}

// ======================================================
// Componente de Card de Documento
// ======================================================
function DocumentCard({ doc, onDelete, onReindex }) {
  const [deleting, setDeleting] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  
  const formatDate = (dateStr) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };
  
  const formatSize = (bytes) => {
    if (!bytes) return "—";
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  };
  
  const handleDelete = async () => {
    if (!confirm(`Remover "${doc.filename}"?`)) return;
    setDeleting(true);
    try {
      await onDelete(doc.id);
    } finally {
      setDeleting(false);
    }
  };
  
  const handleReindex = async () => {
    setReindexing(true);
    try {
      await onReindex(doc.id);
    } finally {
      setReindexing(false);
    }
  };
  
  return (
    <div style={{
      border: "1px solid var(--border-color, #e5e7eb)",
      borderRadius: "8px",
      padding: "16px",
      backgroundColor: "var(--card-bg, #fff)",
      display: "flex",
      flexDirection: "column",
      gap: "12px"
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600 }}>
            {doc.filename}
          </h3>
          <p style={{ margin: "4px 0 0", fontSize: "0.8rem", color: "var(--text-muted, #6b7280)" }}>
            {doc.origin_type?.toUpperCase()} • {formatSize(doc.file_size)}
          </p>
        </div>
        <StatusBadge status={doc.status || "indexed"} />
      </div>
      
      {/* Metadata */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(2, 1fr)",
        gap: "8px",
        fontSize: "0.8rem",
        color: "var(--text-muted, #6b7280)"
      }}>
        <div>
          <strong>Trilha:</strong> {doc.trail_id || "geral"}
        </div>
        <div>
          <strong>Etapa:</strong> {doc.step_id || "geral"}
        </div>
        <div>
          <strong>Versão:</strong> {doc.version || "1.0"}
        </div>
        <div>
          <strong>Chunks:</strong> {doc.chunks_count || "—"}
        </div>
      </div>
      
      {/* Description */}
      {doc.description && (
        <p style={{ 
          margin: 0, 
          fontSize: "0.85rem", 
          color: "var(--text-muted, #6b7280)",
          fontStyle: "italic"
        }}>
          {doc.description}
        </p>
      )}
      
      {/* Footer */}
      <div style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center",
        paddingTop: "8px",
        borderTop: "1px solid var(--border-color, #e5e7eb)"
      }}>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted, #6b7280)" }}>
          Indexado em: {formatDate(doc.indexed_at)}
        </span>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={handleReindex}
            disabled={reindexing}
            style={{
              padding: "4px 8px",
              fontSize: "0.75rem",
              border: "1px solid var(--border-color, #e5e7eb)",
              borderRadius: "4px",
              backgroundColor: "transparent",
              cursor: reindexing ? "not-allowed" : "pointer",
              opacity: reindexing ? 0.6 : 1
            }}
          >
            {reindexing ? "Reindexando..." : "↻ Reindexar"}
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            style={{
              padding: "4px 8px",
              fontSize: "0.75rem",
              border: "1px solid #fee2e2",
              borderRadius: "4px",
              backgroundColor: "#fee2e2",
              color: "#991b1b",
              cursor: deleting ? "not-allowed" : "pointer",
              opacity: deleting ? 0.6 : 1
            }}
          >
            {deleting ? "Removendo..." : "🗑 Remover"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ======================================================
// Componente Principal
// ======================================================
export default function KnowledgePage() {
  const [documents, setDocuments] = useState([]);
  const [trails, setTrails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Form state
  const [file, setFile] = useState(null);
  const [trailId, setTrailId] = useState("geral");
  const [stepId, setStepId] = useState("geral");
  const [description, setDescription] = useState("");
  const [version, setVersion] = useState("1.0");
  
  // Filters
  const [filterTrail, setFilterTrail] = useState("");
  
  const backendBase = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  
  // ======================================================
  // Fetch Documents
  // ======================================================
  const fetchDocuments = useCallback(async () => {
    try {
      const res = await axios.get(`${backendBase}/admin/knowledge`);
      setDocuments(res.data.data || []);
    } catch (err) {
      console.error("Erro ao carregar documentos:", err);
      setError("Não foi possível carregar os documentos");
    }
  }, [backendBase]);
  
  // ======================================================
  // Fetch Trails
  // ======================================================
  const fetchTrails = useCallback(async () => {
    try {
      const res = await axios.get(`${backendBase}/admin/trails`);
      setTrails(res.data || []);
    } catch (err) {
      console.error("Erro ao carregar trilhas:", err);
    }
  }, [backendBase]);
  
  // ======================================================
  // Initial Load
  // ======================================================
  useEffect(() => {
    Promise.all([fetchDocuments(), fetchTrails()])
      .finally(() => setLoading(false));
  }, [fetchDocuments, fetchTrails]);
  
  // ======================================================
  // Upload Handler
  // ======================================================
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Selecione um arquivo para upload");
      return;
    }
    
    // Validate file type
    const allowedTypes = [".pdf", ".pptx", ".docx", ".txt", ".xlsx"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!allowedTypes.includes(ext)) {
      setError(`Tipo de arquivo não suportado. Use: ${allowedTypes.join(", ")}`);
      return;
    }
    
    // Validate file size (50MB max)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      setError("Arquivo muito grande. Máximo: 50MB");
      return;
    }
    
    setUploading(true);
    setUploadProgress(0);
    setError(null);
    setSuccess(null);
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("trail_id", trailId);
    formData.append("step_id", stepId);
    formData.append("description", description);
    formData.append("version", version);
    
    try {
      const res = await axios.post(
        `${backendBase}/admin/knowledge/upload`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (progressEvent) => {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percent);
          }
        }
      );
      
      setSuccess(`✓ "${file.name}" indexado com ${res.data.data?.chunks_indexed || 0} chunks`);
      
      // Reset form
      setFile(null);
      setDescription("");
      setVersion("1.0");
      
      // Refresh list
      await fetchDocuments();
      
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      setError(`Erro no upload: ${detail}`);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };
  
  // ======================================================
  // Delete Handler
  // ======================================================
  const handleDelete = async (docId) => {
    setError(null);
    try {
      await axios.delete(`${backendBase}/admin/knowledge/documents/${docId}`);
      setSuccess("Documento removido com sucesso");
      await fetchDocuments();
    } catch (err) {
      setError(`Erro ao remover: ${err.response?.data?.detail || err.message}`);
    }
  };
  
  // ======================================================
  // Reindex Handler
  // ======================================================
  const handleReindex = async (docId) => {
    setError(null);
    try {
      await axios.post(`${backendBase}/admin/knowledge/reindex/${docId}`);
      setSuccess("Documento reindexado com sucesso");
      await fetchDocuments();
    } catch (err) {
      // Se endpoint não existir, mostrar mensagem
      if (err.response?.status === 404) {
        setError("Funcionalidade de reindexação ainda não implementada no backend");
      } else {
        setError(`Erro ao reindexar: ${err.response?.data?.detail || err.message}`);
      }
    }
  };
  
  // ======================================================
  // Filtered Documents
  // ======================================================
  const filteredDocs = filterTrail
    ? documents.filter(d => d.trail_id === filterTrail)
    : documents;
  
  // ======================================================
  // Render
  // ======================================================
  if (loading) {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <p>Carregando documentos...</p>
      </div>
    );
  }
  
  return (
    <div style={{ maxWidth: "1200px" }}>
      <h1 style={{ marginBottom: "8px" }}>📚 Base de Conhecimento</h1>
      <p style={{ color: "var(--text-muted, #6b7280)", marginBottom: "24px" }}>
        Gerencie os materiais oficiais que o agente FCJ usa como fonte de verdade.
      </p>
      
      {/* Messages */}
      {error && (
        <div style={{
          padding: "12px 16px",
          backgroundColor: "#fee2e2",
          color: "#991b1b",
          borderRadius: "8px",
          marginBottom: "16px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}>
          <span>❌ {error}</span>
          <button onClick={() => setError(null)} style={{ background: "none", border: "none", cursor: "pointer" }}>✕</button>
        </div>
      )}
      
      {success && (
        <div style={{
          padding: "12px 16px",
          backgroundColor: "#dcfce7",
          color: "#166534",
          borderRadius: "8px",
          marginBottom: "16px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}>
          <span>{success}</span>
          <button onClick={() => setSuccess(null)} style={{ background: "none", border: "none", cursor: "pointer" }}>✕</button>
        </div>
      )}
      
      {/* Upload Form */}
      <div style={{
        border: "2px dashed var(--border-color, #e5e7eb)",
        borderRadius: "12px",
        padding: "24px",
        marginBottom: "32px",
        backgroundColor: "var(--card-bg, #f9fafb)"
      }}>
        <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>📤 Upload de Material</h2>
        
        <form onSubmit={handleUpload}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
            {/* File Input */}
            <div style={{ gridColumn: "span 2" }}>
              <label style={{ display: "block", marginBottom: "4px", fontWeight: 500, fontSize: "0.9rem" }}>
                Arquivo (PDF, PPTX, DOCX, TXT)
              </label>
              <input
                type="file"
                accept=".pdf,.pptx,.docx,.txt,.xlsx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                style={{ width: "100%" }}
              />
              {file && (
                <p style={{ margin: "4px 0 0", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Selecionado: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>
            
            {/* Trail Select */}
            <div>
              <label style={{ display: "block", marginBottom: "4px", fontWeight: 500, fontSize: "0.9rem" }}>
                Trilha
              </label>
              <select
                value={trailId}
                onChange={(e) => setTrailId(e.target.value)}
                style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid var(--border-color)" }}
              >
                <option value="geral">Geral (todas as trilhas)</option>
                {trails.map(t => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>
            
            {/* Step Input */}
            <div>
              <label style={{ display: "block", marginBottom: "4px", fontWeight: 500, fontSize: "0.9rem" }}>
                Etapa
              </label>
              <input
                type="text"
                value={stepId}
                onChange={(e) => setStepId(e.target.value)}
                placeholder="Ex: ICP, Persona, SWOT..."
                style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid var(--border-color)" }}
              />
            </div>
            
            {/* Version */}
            <div>
              <label style={{ display: "block", marginBottom: "4px", fontWeight: 500, fontSize: "0.9rem" }}>
                Versão
              </label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="1.0"
                style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid var(--border-color)" }}
              />
            </div>
            
            {/* Description */}
            <div>
              <label style={{ display: "block", marginBottom: "4px", fontWeight: 500, fontSize: "0.9rem" }}>
                Descrição
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Breve descrição do material..."
                style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid var(--border-color)" }}
              />
            </div>
          </div>
          
          {/* Progress Bar */}
          {uploading && (
            <div style={{ marginBottom: "16px" }}>
              <div style={{
                height: "8px",
                backgroundColor: "#e5e7eb",
                borderRadius: "4px",
                overflow: "hidden"
              }}>
                <div style={{
                  height: "100%",
                  width: `${uploadProgress}%`,
                  backgroundColor: "#3b82f6",
                  transition: "width 0.3s ease"
                }} />
              </div>
              <p style={{ margin: "4px 0 0", fontSize: "0.8rem", textAlign: "center" }}>
                {uploadProgress < 100 ? `Enviando... ${uploadProgress}%` : "Processando documento..."}
              </p>
            </div>
          )}
          
          <button
            type="submit"
            disabled={uploading || !file}
            className="btn btn-primary"
            style={{
              padding: "12px 24px",
              fontSize: "1rem",
              opacity: (uploading || !file) ? 0.6 : 1,
              cursor: (uploading || !file) ? "not-allowed" : "pointer"
            }}
          >
            {uploading ? "Processando..." : "📤 Enviar e Indexar"}
          </button>
        </form>
      </div>
      
      {/* Documents List */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h2 style={{ margin: 0 }}>📄 Documentos Indexados ({filteredDocs.length})</h2>
          
          {/* Filter */}
          <select
            value={filterTrail}
            onChange={(e) => setFilterTrail(e.target.value)}
            style={{ padding: "8px", borderRadius: "4px", border: "1px solid var(--border-color)" }}
          >
            <option value="">Todas as trilhas</option>
            <option value="geral">Geral</option>
            {trails.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>
        
        {filteredDocs.length === 0 ? (
          <div style={{
            padding: "40px",
            textAlign: "center",
            border: "1px dashed var(--border-color)",
            borderRadius: "8px",
            color: "var(--text-muted)"
          }}>
            <p>Nenhum documento indexado ainda.</p>
            <p style={{ fontSize: "0.9rem" }}>Faça upload dos materiais da FCJ acima.</p>
          </div>
        ) : (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))",
            gap: "16px"
          }}>
            {filteredDocs.map(doc => (
              <DocumentCard
                key={doc.id}
                doc={doc}
                onDelete={handleDelete}
                onReindex={handleReindex}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

