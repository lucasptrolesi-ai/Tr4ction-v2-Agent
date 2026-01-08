"use client";

import { ShieldAlert } from "lucide-react";

const COLORS = {
  LOW: { bg: "#ecfdf3", text: "#15803d", border: "#bbf7d0" },
  MEDIUM: { bg: "#fffbeb", text: "#b45309", border: "#fef3c7" },
  HIGH: { bg: "#fef2f2", text: "#b91c1c", border: "#fecdd3" },
  CRITICAL: { bg: "#fef2f2", text: "#991b1b", border: "#fecdd3" },
};

export default function RiskBadge({ level }) {
  if (!level) return null;
  
  const normalized = String(level).toUpperCase();
  const palette = COLORS[normalized] || COLORS.LOW;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "8px",
        padding: "8px 12px",
        borderRadius: "999px",
        background: palette.bg,
        color: palette.text,
        border: `1px solid ${palette.border}`,
        fontWeight: 600,
        fontSize: "0.9rem",
      }}
      role="status"
      aria-label={`Nível de risco: ${normalized}`}
    >
      <ShieldAlert size={16} aria-hidden="true" />
      <span style={{ letterSpacing: "0.5px" }}>{normalized}</span>
    </div>
  );
}
