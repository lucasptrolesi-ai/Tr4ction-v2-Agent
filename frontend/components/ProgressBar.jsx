"use client";

import { CheckCircle } from "lucide-react";

/**
 * Barra de progresso visual para etapas
 */
export default function ProgressBar({ 
  current = 0, 
  total = 100, 
  showPercentage = true,
  showLabel = true,
  size = "default" // "small", "default", "large"
}) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
  const isComplete = percentage >= 100;

  const getColor = () => {
    if (isComplete) return "#10b981";
    if (percentage >= 75) return "#22c55e";
    if (percentage >= 50) return "#f59e0b";
    if (percentage > 0) return "#3b82f6";
    return "#e5e7eb";
  };

  const getHeight = () => {
    switch (size) {
      case "small": return "6px";
      case "large": return "16px";
      default: return "10px";
    }
  };

  return (
    <div className="progress-bar-container">
      {showLabel && (
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "6px",
          fontSize: size === "small" ? "0.75rem" : "0.85rem"
        }}>
          <span style={{ color: "var(--text-muted)" }}>
            Progresso
          </span>
          <span style={{ 
            color: isComplete ? "#10b981" : "var(--text-primary)",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: "4px"
          }}>
            {isComplete && <CheckCircle size={14} />}
            {showPercentage && `${percentage}%`}
          </span>
        </div>
      )}

      <div style={{
        width: "100%",
        height: getHeight(),
        background: "#e5e7eb",
        borderRadius: "999px",
        overflow: "hidden"
      }}>
        <div 
          style={{
            width: `${percentage}%`,
            height: "100%",
            background: getColor(),
            borderRadius: "999px",
            transition: "width 0.5s ease, background 0.3s ease"
          }}
        />
      </div>

      {!showLabel && showPercentage && (
        <div style={{
          textAlign: "center",
          marginTop: "4px",
          fontSize: "0.75rem",
          color: "var(--text-muted)"
        }}>
          {percentage}%
        </div>
      )}
    </div>
  );
}

/**
 * Indicador de campos preenchidos
 */
export function FieldsProgress({ filled, total }) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "8px",
      fontSize: "0.85rem",
      color: "var(--text-muted)"
    }}>
      <span>{filled} de {total} campos preenchidos</span>
      <ProgressBar 
        current={filled} 
        total={total} 
        showLabel={false}
        showPercentage={false}
        size="small"
      />
    </div>
  );
}

/**
 * Badge de status da etapa
 */
export function StepStatusBadge({ status, progress = 0 }) {
  const getConfig = () => {
    if (status === "completed" || progress >= 100) {
      return {
        label: "Concluído",
        bg: "#dcfce7",
        color: "#166534",
        icon: "✓"
      };
    }
    if (status === "locked") {
      return {
        label: "Bloqueado",
        bg: "#f3f4f6",
        color: "#6b7280",
        icon: "🔒"
      };
    }
    if (progress > 0) {
      return {
        label: `${progress}%`,
        bg: "#fef3c7",
        color: "#92400e",
        icon: "⏳"
      };
    }
    return {
      label: "Não iniciado",
      bg: "#f3f4f6",
      color: "#6b7280",
      icon: "○"
    };
  };

  const config = getConfig();

  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: "4px",
      padding: "4px 10px",
      fontSize: "0.8rem",
      fontWeight: 500,
      background: config.bg,
      color: config.color,
      borderRadius: "999px"
    }}>
      <span>{config.icon}</span>
      {config.label}
    </span>
  );
}
