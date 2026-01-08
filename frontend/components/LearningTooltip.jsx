"use client";

import { useState } from "react";
import { Lightbulb } from "lucide-react";

export default function LearningTooltip({ text, label = "Como melhorar" }) {
  const [open, setOpen] = useState(false);
  
  if (!text || typeof text !== "string" || !text.trim()) return null;

  const safeLabel = label && typeof label === "string" ? label : "Como melhorar";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        aria-label={safeLabel}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "8px",
          padding: "8px 10px",
          background: "#f1f5f9",
          border: "1px solid #e2e8f0",
          borderRadius: "8px",
          color: "#0f172a",
          fontWeight: 600,
          cursor: "pointer",
          fontSize: "0.9rem",
        }}
      >
        <Lightbulb size={16} aria-hidden="true" />
        {safeLabel}
      </button>

      {open && (
        <div
          style={{
            padding: "12px 14px",
            borderRadius: "10px",
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            color: "#0f172a",
            fontSize: "0.92rem",
            lineHeight: 1.5,
          }}
          role="region"
          aria-label="Orientação"
        >
          {text}
        </div>
      )}
    </div>
  );
}
