"use client";

import { useState, useEffect, useCallback } from "react";
import axios from "axios";

// ======================================================
// SVG Icons
// ======================================================
const UploadIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M17 8L12 3L7 8M12 3V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const FileIcon = ({ type }) => {
  const icons = {
    pdf: "📕",
    pptx: "📊",
    docx: "📘",
    txt: "📄",
    xlsx: "📗",
  };
  return <span style={{ fontSize: "24px" }}>{icons[type] || "📄"}</span>;
};

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
  const [expanded, setExpanded] = useState(false);
  
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

  const fileExt = doc.filename?.split(".").pop().toLowerCase();
  
  return (
    <div style={{
      background: "rgba(255, 255, 255, 0.04)",
      border: "1px solid rgba(255, 255, 255, 0.08)",
      borderRadius: "12px",
      padding: "20px",
      backdropFilter: "blur(10px)",
      transition: "all 0.2s ease",
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.background = "rgba(255, 255, 255, 0.06)";
      e.currentTarget.style.borderColor = "rgba(99, 102, 241, 0.3)";
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.background = "rgba(255, 255, 255, 0.04)";
      e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
        <div style={{ display: "flex", gap: "12px", flex: 1 }}>
          <FileIcon type={fileExt} />
          <div style={{ flex: 1 }}>
            <h3 style={{ margin: "0 0 6px", fontSize: "15px", fontWeight: 600, color: "#f8fafc" }}>
              {doc.filename}
            </h3>
            <div style={{ display: "flex", gap: "12px", fontSize: "12px", color: "#64748b" }}>
              <span>📁 {formatSize(doc.file_size)}</span>
              <span>🏷️ {doc.origin_type?.toUpperCase() || "N/A"}</span>
              <span>📦 {doc.chunks_count || 0} chunks</span>
            </div>
          </div>
        </div>
        <StatusBadge status={doc.status || "indexed"} />
      </div>
      
      {/* Metadata Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
        gap: "12px",
        padding: "16px",
        background: "rgba(0, 0, 0, 0.2)",
        borderRadius: "8px",
        marginBottom: "16px",
      }}>
        <div>
          <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>Trilha</div>
          <div style={{ fontSize: "13px", color: "#f8fafc", fontWeight: 500 }}>
            {doc.trail_id || "geral"}
          </div>
        </div>
        <div>
          <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>Etapa</div>
          <div style={{ fontSize: "13px", color: "#f8fafc", fontWeight: 500 }}>
            {doc.step_id || "geral"}
          </div>
        </div>
        <div>
          <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>Versão</div>
          <div style={{ fontSize: "13px", color: "#f8fafc", fontWeight: 500 }}>
            {doc.version || "1.0"}
          </div>
        </div>
        <div>
          <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>Indexado</div>
          <div style={{ fontSize: "13px", color: "#f8fafc", fontWeight: 500 }}>
            {formatDate(doc.indexed_at)}
          </div>
        </div>
      </div>
      
      {/* Description */}
      {doc.description && (
        <p style={{ 
          margin: "0 0 16px", 
          fontSize: "13px", 
          color: "#94a3b8",
          lineHeight: "1.6",
          fontStyle: "italic",
          padding: "12px",
          background: "rgba(0, 0, 0, 0.2)",
          borderRadius: "8px",
           borderLeft: "3px solid #00BCD4",
        }}>
          💬 {doc.description}
        </p>
      )}
      
      {/* Actions */}
      <div style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center",
        paddingTop: "16px",
        borderTop: "1px solid rgba(255, 255, 255, 0.08)"
      }}>
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            padding: "6px 12px",
            fontSize: "12px",
            background: "transparent",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: "6px",
            color: "#94a3b8",
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
            e.currentTarget.style.color = "#f8fafc";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.color = "#94a3b8";
          }}
        >
          {expanded ? "▲ Menos detalhes" : "▼ Mais detalhes"}
        </button>
        
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={handleReindex}
            disabled={reindexing}
            style={{
              padding: "6px 12px",
              fontSize: "12px",
              border: "1px solid rgba(14, 165, 233, 0.3)",
              borderRadius: "6px",
              background: "rgba(14, 165, 233, 0.1)",
              color: reindexing ? "#64748b" : "#00BCD4",
              cursor: reindexing ? "not-allowed" : "pointer",
              fontWeight: 500,
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              if (!reindexing) {
                e.currentTarget.style.background = "rgba(14, 165, 233, 0.2)";
              }
            }}
            onMouseLeave={(e) => {
              if (!reindexing) {
                e.currentTarget.style.background = "rgba(14, 165, 233, 0.1)";
              }
            }}
          >
            {reindexing ? "⏳ Processando..." : "↻ Reindexar"}
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            style={{
              padding: "6px 12px",
              fontSize: "12px",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              borderRadius: "6px",
              background: "rgba(239, 68, 68, 0.1)",
              color: deleting ? "#64748b" : "#ef4444",
              cursor: deleting ? "not-allowed" : "pointer",
              fontWeight: 500,
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              if (!deleting) {
                e.currentTarget.style.background = "rgba(239, 68, 68, 0.2)";
              }
            }}
            onMouseLeave={(e) => {
              if (!deleting) {
                e.currentTarget.style.background = "rgba(239, 68, 68, 0.1)";
              }
            }}
          >
            {deleting ? "⏳ Removendo..." : "🗑 Remover"}
          </button>
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div style={{
          marginTop: "16px",
          padding: "16px",
          background: "rgba(0, 0, 0, 0.3)",
          borderRadius: "8px",
          fontSize: "12px",
          color: "#94a3b8",
          lineHeight: "1.8",
        }}>
          <div><strong>Document ID:</strong> {doc.id}</div>
          <div><strong>Upload Path:</strong> {doc.file_path || "N/A"}</div>
          <div><strong>Content Type:</strong> {doc.content_type || "N/A"}</div>
          <div><strong>Embedding Model:</strong> {doc.embedding_model || "default"}</div>
        </div>
      )}
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
      <div style={{ textAlign: "center", padding: "60px", color: "#94a3b8" }}>
        <div style={{ fontSize: "40px", marginBottom: "16px" }}>⏳</div>
        <div>Carregando base de conhecimento...</div>
      </div>
    );
  }
  
  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "32px" }}>
        <h1 style={{
          margin: "0 0 8px",
          fontSize: "28px",
          fontWeight: "700",
          color: "#f8fafc",
        }}>
          📚 Base de Conhecimento
        </h1>
        <p style={{ margin: 0, fontSize: "15px", color: "#64748b" }}>
          Materiais oficiais FCJ que alimentam o agente TR4CTION com RAG (Retrieval-Augmented Generation)
        </p>
      </div>
      
      {/* Messages */}
      {error && (
        <div style={{
          padding: "16px 20px",
          background: "rgba(239, 68, 68, 0.1)",
          border: "1px solid rgba(239, 68, 68, 0.3)",
          borderRadius: "12px",
          marginBottom: "20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          color: "#fca5a5",
        }}>
          <span>❌ {error}</span>
          <button 
            onClick={() => setError(null)} 
            style={{ 
              background: "none", 
              border: "none", 
              cursor: "pointer", 
              color: "#fca5a5",
              fontSize: "18px",
            }}
          >
            ✕
          </button>
        </div>
      )}
      
      {success && (
        <div style={{
          padding: "16px 20px",
          background: "rgba(34, 197, 94, 0.1)",
          border: "1px solid rgba(34, 197, 94, 0.3)",
          borderRadius: "12px",
          marginBottom: "20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          color: "#86efac",
        }}>
          <span>{success}</span>
          <button 
            onClick={() => setSuccess(null)} 
            style={{ 
              background: "none", 
              border: "none", 
              cursor: "pointer", 
              color: "#86efac",
              fontSize: "18px",
            }}
          >
            ✕
          </button>
        </div>
      )}
      
      {/* Upload Form */}
      <div style={{
        background: "rgba(0, 188, 212, 0.05)",
        border: "2px dashed rgba(0, 188, 212, 0.3)",
        borderRadius: "16px",
        padding: "32px",
        marginBottom: "40px",
      }}>
        <div style={{ textAlign: "center", marginBottom: "24px" }}>
          <div style={{ color: "#00BCD4", marginBottom: "12px" }}>
            <UploadIcon />
          </div>
          <h2 style={{ margin: "0 0 8px", fontSize: "20px", fontWeight: "600", color: "#f8fafc" }}>
            📤 Upload de Material
          </h2>
          <p style={{ margin: 0, fontSize: "13px", color: "#94a3b8" }}>
            Suporta: PDF, PPTX, DOCX, TXT, XLSX • Tamanho máximo: 50MB
          </p>
        </div>
        
        <form onSubmit={handleUpload}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
            {/* File Input */}
            <div style={{ gridColumn: "span 2" }}>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: 500, fontSize: "13px", color: "#f8fafc" }}>
                Arquivo
              </label>
              <input
                type="file"
                accept=".pdf,.pptx,.docx,.txt,.xlsx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                style={{ 
                  width: "100%", 
                  padding: "12px",
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "8px",
                  color: "#f8fafc",
                  fontSize: "14px",
                }}
              />
              {file && (
                <p style={{ margin: "8px 0 0", fontSize: "12px", color: "#94a3b8" }}>
                  ✓ Selecionado: <strong>{file.name}</strong> ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>
            
            {/* Trail Select */}
            <div>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: 500, fontSize: "13px", color: "#f8fafc" }}>
                Trilha
              </label>
              <select
                value={trailId}
                onChange={(e) => setTrailId(e.target.value)}
                style={{ 
                  width: "100%", 
                  padding: "10px",
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "8px",
                  color: "#f8fafc",
                  fontSize: "14px",
                }}
              >
                <option value="geral" style={{ background: "#1e293b" }}>🌐 Geral (todas as trilhas)</option>
                {trails.map(t => (
                  <option key={t.id} value={t.id} style={{ background: "#1e293b" }}>{t.name}</option>
                ))}
              </select>
            </div>
            
            {/* Step Input */}
            <div>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: 500, fontSize: "13px", color: "#f8fafc" }}>
                Etapa
              </label>
              <input
                type="text"
                value={stepId}
                onChange={(e) => setStepId(e.target.value)}
                placeholder="Ex: ICP, Persona, SWOT..."
                style={{ 
                  width: "100%", 
                  padding: "10px",
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "8px",
                  color: "#f8fafc",
                  fontSize: "14px",
                }}
              />
            </div>
            
            {/* Version */}
            <div>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: 500, fontSize: "13px", color: "#f8fafc" }}>
                Versão
              </label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="1.0"
                style={{ 
                  width: "100%", 
                  padding: "10px",
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "8px",
                  color: "#f8fafc",
                  fontSize: "14px",
                }}
              />
            </div>
            
            {/* Description */}
            <div>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: 500, fontSize: "13px", color: "#f8fafc" }}>
                Descrição
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Breve descrição do material..."
                style={{ 
                  width: "100%", 
                  padding: "10px",
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "8px",
                  color: "#f8fafc",
                  fontSize: "14px",
                }}
              />
            </div>
          </div>
          
          {/* Progress Bar */}
          {uploading && (
            <div style={{ marginBottom: "20px" }}>
              <div style={{
                height: "8px",
                background: "rgba(0, 0, 0, 0.3)",
                borderRadius: "999px",
                overflow: "hidden"
              }}>
                <div style={{
                  height: "100%",
                  width: `${uploadProgress}%`,
                  background: "linear-gradient(90deg, #00BCD4 0%, #00ACC1 100%)",
                  transition: "width 0.3s ease",
                  boxShadow: "0 0 10px #00BCD4",
                }}></div>
              </div>
              <p style={{ margin: "8px 0 0", fontSize: "12px", color: "#94a3b8", textAlign: "center" }}>
                Processando... {uploadProgress}%
              </p>
            </div>
          )}
          
          {/* Submit Button */}
          <button
            type="submit"
            disabled={uploading || !file}
            style={{
              width: "100%",
              padding: "14px",
              background: uploading || !file 
                ? "rgba(100, 116, 139, 0.3)"
                 : "linear-gradient(135deg, #00BCD4 0%, #00ACC1 100%)",
              color: "white",
              border: "none",
              borderRadius: "10px",
              cursor: uploading || !file ? "not-allowed" : "pointer",
              fontSize: "15px",
              fontWeight: "600",
              transition: "all 0.2s ease",
              boxShadow: uploading || !file ? "none" : "0 4px 14px rgba(0, 188, 212, 0.4)",
            }}
          >
            {uploading ? "⏳ Indexando documento..." : "🚀 Indexar Documento"}
          </button>
        </form>
      </div>
      
      {/* Stats & Filters */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "24px",
        padding: "20px",
        background: "rgba(255, 255, 255, 0.03)",
        borderRadius: "12px",
        border: "1px solid rgba(255, 255, 255, 0.08)",
      }}>
        <div>
          <div style={{ fontSize: "13px", color: "#64748b", marginBottom: "4px" }}>
            Total de Documentos
          </div>
          <div style={{ fontSize: "24px", fontWeight: "700", color: "#f8fafc" }}>
            {filteredDocs.length}
          </div>
        </div>
        
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <label style={{ fontSize: "13px", color: "#94a3b8" }}>Filtrar por trilha:</label>
          <select
            value={filterTrail}
            onChange={(e) => setFilterTrail(e.target.value)}
            style={{
              padding: "8px 12px",
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              color: "#f8fafc",
              fontSize: "13px",
            }}
          >
            <option value="" style={{ background: "#1e293b" }}>Todas</option>
            <option value="geral" style={{ background: "#1e293b" }}>Geral</option>
            {trails.map(t => (
              <option key={t.id} value={t.id} style={{ background: "#1e293b" }}>{t.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Documents List */}
      <div>
        <h3 style={{ margin: "0 0 20px", fontSize: "18px", fontWeight: "600", color: "#f8fafc" }}>
          📦 Documentos Indexados
        </h3>
        
        {filteredDocs.length === 0 ? (
          <div style={{
            textAlign: "center",
            padding: "60px 20px",
            background: "rgba(255, 255, 255, 0.03)",
            borderRadius: "12px",
            border: "1px dashed rgba(255, 255, 255, 0.1)",
          }}>
            <div style={{ fontSize: "48px", marginBottom: "16px" }}>📭</div>
            <div style={{ fontSize: "16px", color: "#94a3b8", marginBottom: "8px" }}>
              Nenhum documento encontrado
            </div>
            <div style={{ fontSize: "13px", color: "#64748b" }}>
              {filterTrail ? "Tente outro filtro ou faça upload de novos materiais" : "Faça upload do primeiro material FCJ"}
            </div>
          </div>
        ) : (
          <div style={{ display: "grid", gap: "20px" }}>
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
