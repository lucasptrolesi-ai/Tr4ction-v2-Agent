"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, useEffect, useMemo, useCallback } from "react";
import ChatWidget from "@/components/ChatWidget";
import DynamicField from "@/components/DynamicField";
import ProgressBar, { FieldsProgress } from "@/components/ProgressBar";
import { 
  Lock, Save, CheckCircle, Download, WifiOff, 
  ArrowLeft, ArrowRight, AlertTriangle 
} from "lucide-react";
import { apiGet, apiPost } from "@/lib/api";

export default function FounderTemplateStepPage() {
  const params = useParams();
  const router = useRouter();
  const { trailId, stepId } = params;

  // Estados principais
  const [schema, setSchema] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const [offline, setOffline] = useState(false);
  const [showValidation, setShowValidation] = useState(false);
  const [allSteps, setAllSteps] = useState([]);
  const [chatContext, setChatContext] = useState("");

  // Calcular progresso
  const progress = useMemo(() => {
    if (!schema?.fields?.length) return { filled: 0, total: 0, percentage: 0 };
    
    const fields = schema.fields;
    const total = fields.length;
    const filled = fields.filter(f => {
      const fieldName = f.name || f.key;
      const value = formData[fieldName];
      return value && value.toString().trim() !== "";
    }).length;
    
    return {
      filled,
      total,
      percentage: Math.round((filled / total) * 100)
    };
  }, [schema, formData]);

  // Validar campos obrigatórios
  const validation = useMemo(() => {
    if (!schema?.fields?.length) return { isValid: true, errors: [] };
    
    const errors = [];
    schema.fields.forEach(f => {
      if (f.required) {
        const fieldName = f.name || f.key;
        const value = formData[fieldName];
        if (!value || value.toString().trim() === "") {
          errors.push({ field: fieldName, label: f.label });
        }
      }
    });
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }, [schema, formData]);

  // Navegação entre steps
  const navigation = useMemo(() => {
    const currentIndex = allSteps.findIndex(s => s.id === stepId);
    return {
      currentIndex,
      hasPrev: currentIndex > 0,
      hasNext: currentIndex < allSteps.length - 1,
      prevStep: currentIndex > 0 ? allSteps[currentIndex - 1] : null,
      nextStep: currentIndex < allSteps.length - 1 ? allSteps[currentIndex + 1] : null
    };
  }, [allSteps, stepId]);

  useEffect(() => {
    loadStepData();
  }, [trailId, stepId]);

  async function loadStepData() {
    try {
      setLoading(true);
      setOffline(false);
      
      // Carregar lista de steps da trilha
      try {
        const trailsData = await apiGet("/founder/trails");
        const trail = trailsData?.find(t => t.id === trailId);
        if (trail?.steps) {
          setAllSteps(trail.steps);
        }
      } catch (err) {
        console.warn("Não foi possível carregar lista de steps:", err);
      }

      // Carregar schema da etapa - ENDPOINT /founder/
      let schemaData = null;
      try {
        schemaData = await apiGet(`/founder/trails/${trailId}/steps/${stepId}/schema`);
      } catch {
        // Fallback para endpoint admin
        try {
          schemaData = await apiGet(`/admin/trails/${trailId}/steps/${stepId}/schema`);
        } catch {
          console.warn("Schema não encontrado, usando fallback");
        }
      }

      if (schemaData?.fields) {
        setSchema(schemaData);
      } else {
        // Fallback mínimo
        setSchema({
          step_id: stepId,
          step_name: stepId.charAt(0).toUpperCase() + stepId.slice(1),
          fields: []
        });
      }

      // Carregar progresso salvo
      try {
        const progressData = await apiGet(`/founder/trails/${trailId}/steps/${stepId}/progress`);
        if (progressData) {
          setFormData(progressData.formData || {});
          setIsLocked(progressData.isLocked || false);
        }
      } catch {
        setFormData({});
      }
    } catch (err) {
      console.error("Erro ao carregar dados:", err);
      setOffline(true);
      setIsLocked(false);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(silent = false) {
    try {
      setSaving(true);
      
      if (offline) {
        // Salva localmente
        localStorage.setItem(
          `tr4ction_${trailId}_${stepId}`, 
          JSON.stringify(formData)
        );
        setLastSaved(new Date().toLocaleTimeString());
        return true;
      }
      
      await apiPost(`/founder/trails/${trailId}/steps/${stepId}/progress`, { formData });
      setLastSaved(new Date().toLocaleTimeString());
      
      return true;
    } catch (err) {
      console.error("Erro ao salvar:", err);
      if (!silent) {
        alert("Erro ao salvar: " + err.message);
      }
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function handleDownload() {
    try {
      if (offline) {
        alert("Download disponível quando o backend estiver ativo.");
        return;
      }
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
      window.open(`${apiBase}/founder/trails/${trailId}/export/xlsx`, "_blank");
    } catch (err) {
      console.error("Erro ao baixar:", err);
      alert("Erro ao baixar: " + err.message);
    }
  }

  function handleFieldChange(fieldName, value) {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
  }

  // Handler para perguntar à IA sobre um campo específico
  const handleAskAI = useCallback((field) => {
    const question = `Me ajude a preencher o campo "${field.label}" ${
      field.help ? `(dica: ${field.help})` : ""
    }. O que devo considerar?`;
    
    setChatContext(
      `Etapa: ${schema?.step_name || stepId}. ` +
      `Campo atual: ${field.label}. ` +
      `Tipo: ${field.type}. ` +
      (field.placeholder ? `Exemplo: ${field.placeholder}. ` : "")
    );
    
    // Dispara evento para abrir chat com pergunta
    window.dispatchEvent(new CustomEvent("openChatWithQuestion", { 
      detail: { question } 
    }));
  }, [schema, stepId]);

  async function handleNext() {
    // Valida antes de avançar
    if (!validation.isValid) {
      setShowValidation(true);
      alert(`Preencha os campos obrigatórios antes de continuar:\n\n${
        validation.errors.map(e => `• ${e.label}`).join("\n")
      }`);
      return;
    }

    // Salva e avança
    const saved = await handleSave(true);
    if (saved && navigation.nextStep && !navigation.nextStep.locked) {
      router.push(`/founder/templates/${trailId}/${navigation.nextStep.id}`);
    }
  }

  function handlePrev() {
    if (navigation.prevStep) {
      handleSave(true);
      router.push(`/founder/templates/${trailId}/${navigation.prevStep.id}`);
    }
  }

  // Loading state
  if (loading) {
    return (
      <div style={{ padding: "60px", textAlign: "center" }}>
        <div className="loading-spinner" style={{ marginBottom: "16px" }}>
          <div style={{
            width: "40px",
            height: "40px",
            border: "3px solid #e5e7eb",
            borderTopColor: "var(--primary)",
            borderRadius: "50%",
            animation: "spin 1s linear infinite",
            margin: "0 auto"
          }} />
        </div>
        <div style={{ fontSize: "1.1rem", color: "var(--text-muted)" }}>
          Carregando formulário...
        </div>
        <style jsx>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Locked state
  if (isLocked) {
    return (
      <div style={{ padding: "60px", textAlign: "center" }}>
        <Lock size={64} style={{ color: "#94a3b8", marginBottom: "24px" }} />
        <h2 style={{ marginBottom: "12px" }}>Etapa Bloqueada</h2>
        <p style={{ color: "var(--text-muted)", maxWidth: "500px", margin: "0 auto 32px" }}>
          Complete as etapas anteriores para desbloquear esta. 
          O administrador pode liberar etapas específicas se necessário.
        </p>
        <button 
          onClick={() => router.push(`/founder/templates`)} 
          className="btn btn-primary"
        >
          <ArrowLeft size={16} style={{ marginRight: "8px" }} />
          Voltar para Trilhas
        </button>
      </div>
    );
  }

  // Contexto completo para o chat
  const fullChatContext = chatContext || (schema 
    ? `Etapa: ${schema.step_name}. Campos: ${schema.fields?.map(f => f.label).join(", ")}.`
    : ""
  );

  return (
    <div style={{ position: "relative", minHeight: "100vh", paddingBottom: "100px" }}>
      {/* Header Sticky */}
      <div style={{ 
        padding: "20px 32px", 
        borderBottom: "1px solid var(--border)",
        background: "#fff",
        position: "sticky",
        top: 0,
        zIndex: 20
      }}>
        {/* Offline Banner */}
        {offline && (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "8px 12px",
            background: "#fef3c7",
            borderRadius: "8px",
            marginBottom: "16px",
            fontSize: "0.85rem",
            color: "#92400e"
          }}>
            <WifiOff size={16} />
            Modo offline - alterações salvas localmente
          </div>
        )}

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div style={{ flex: 1 }}>
            {/* Breadcrumb */}
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: "8px", 
              marginBottom: "12px",
              fontSize: "0.85rem",
              color: "var(--text-muted)"
            }}>
              <button 
                onClick={() => router.push("/founder/templates")} 
                className="btn btn-ghost"
                style={{ padding: "4px 8px", fontSize: "0.85rem" }}
              >
                Trilhas
              </button>
              <span>/</span>
              <span>{trailId}</span>
              <span>/</span>
              <span style={{ color: "var(--primary)", fontWeight: 500 }}>{schema?.step_name || stepId}</span>
            </div>

            <h1 style={{ margin: 0, marginBottom: "8px" }}>
              {schema?.step_name || stepId}
            </h1>

            {/* Progress indicator */}
            <div style={{ maxWidth: "300px", marginTop: "12px" }}>
              <FieldsProgress filled={progress.filled} total={progress.total} />
            </div>
          </div>
          
          {/* Actions */}
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            {lastSaved && (
              <span style={{ 
                fontSize: "0.8rem", 
                color: "#10b981",
                display: "flex",
                alignItems: "center",
                gap: "4px"
              }}>
                <CheckCircle size={14} />
                Salvo às {lastSaved}
              </span>
            )}
            
            <button 
              onClick={() => handleSave(false)} 
              disabled={saving}
              className="btn btn-secondary"
              style={{ display: "flex", alignItems: "center", gap: "6px" }}
            >
              <Save size={16} />
              {saving ? "Salvando..." : "Salvar"}
            </button>
            
            <button 
              onClick={handleDownload}
              className="btn btn-ghost"
              style={{ display: "flex", alignItems: "center", gap: "6px" }}
            >
              <Download size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Form Content */}
      <div style={{ 
        maxWidth: "800px", 
        margin: "0 auto", 
        padding: "40px 32px"
      }}>
        {/* Aviso de validação */}
        {showValidation && !validation.isValid && (
          <div style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "12px",
            padding: "16px",
            background: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: "12px",
            marginBottom: "32px"
          }}>
            <AlertTriangle size={20} style={{ color: "#dc2626", flexShrink: 0, marginTop: "2px" }} />
            <div>
              <div style={{ fontWeight: 600, color: "#991b1b", marginBottom: "4px" }}>
                Campos obrigatórios pendentes
              </div>
              <div style={{ fontSize: "0.9rem", color: "#7f1d1d" }}>
                {validation.errors.map(e => e.label).join(", ")}
              </div>
            </div>
          </div>
        )}

        {/* Campos dinâmicos */}
        {schema?.fields?.length > 0 ? (
          <form onSubmit={(e) => { e.preventDefault(); handleSave(); }}>
            {schema.fields.map((field) => (
              <div key={field.name || field.key} className="card" style={{ marginBottom: "20px" }}>
                <DynamicField
                  field={field}
                  value={formData[field.name || field.key]}
                  onChange={handleFieldChange}
                  onAskAI={handleAskAI}
                  showValidation={showValidation}
                />
              </div>
            ))}
          </form>
        ) : (
          <div className="card" style={{ textAlign: "center", padding: "40px" }}>
            <p style={{ color: "var(--text-muted)" }}>
              Nenhum campo configurado para esta etapa.
            </p>
          </div>
        )}

        {/* Navigation between steps */}
        {allSteps.length > 1 && (
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: "48px",
            paddingTop: "24px",
            borderTop: "1px solid var(--border)"
          }}>
            <button
              onClick={handlePrev}
              disabled={!navigation.hasPrev}
              className="btn btn-ghost"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                opacity: navigation.hasPrev ? 1 : 0.4
              }}
            >
              <ArrowLeft size={18} />
              {navigation.prevStep?.name || "Anterior"}
            </button>

            <div style={{ 
              fontSize: "0.85rem", 
              color: "var(--text-muted)" 
            }}>
              Etapa {navigation.currentIndex + 1} de {allSteps.length}
            </div>

            <button
              onClick={handleNext}
              disabled={!navigation.hasNext || navigation.nextStep?.locked}
              className="btn btn-primary"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                opacity: navigation.hasNext && !navigation.nextStep?.locked ? 1 : 0.4
              }}
            >
              {navigation.nextStep?.name || "Próxima"}
              {navigation.nextStep?.locked ? (
                <Lock size={16} />
              ) : (
                <ArrowRight size={18} />
              )}
            </button>
          </div>
        )}

        {/* Barra de progresso geral */}
        <div style={{ marginTop: "48px" }}>
          <ProgressBar 
            current={progress.percentage} 
            total={100}
            showLabel={true}
          />
        </div>
      </div>

      {/* Chat Widget */}
      <ChatWidget context={fullChatContext} />
    </div>
  );
}
