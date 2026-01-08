"use client";

import { AlertOctagon } from "lucide-react";

export default function StrategicAlert({ text }) {
  if (!text || typeof text !== "string" || !text.trim()) return null;

  return (
    <div
      style={{
        display: "flex",
        gap: "10px",
        alignItems: "flex-start",
        padding: "12px 14px",
        borderRadius: "10px",
        background: "#fff7ed",
        border: "1px solid #fed7aa",
        color: "#9a3412",
        fontSize: "0.95rem",
        lineHeight: 1.4,
      }}
      role="alert"
      aria-live="polite"
    >
      <AlertOctagon size={18} style={{ flexShrink: 0 }} aria-hidden="true" />
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <span style={{ fontWeight: 700 }}>Atenção</span>
        <span>{text}</span>
      </div>
    </div>
  );
}
