"use client";

import { Link2 } from "lucide-react";

export default function DependencyHint({ items }) {
  if (!items || !Array.isArray(items) || items.length === 0) return null;

  const validItems = items.filter((item) => item && typeof item === "string" && item.trim());
  if (validItems.length === 0) return null;

  return (
    <div
      style={{
        padding: "12px 14px",
        borderRadius: "10px",
        background: "#eff6ff",
        border: "1px solid #bfdbfe",
        color: "#1d4ed8",
        fontSize: "0.9rem",
        display: "flex",
        flexDirection: "column",
        gap: "8px",
      }}
      role="complementary"
      aria-label="Dependências estratégicas"
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700 }}>
        <Link2 size={16} aria-hidden="true" />
        <span>Dependências</span>
      </div>
      <ul style={{ margin: 0, paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "6px" }}>
        {validItems.map((item, idx) => (
          <li key={`dep-${idx}-${item.substring(0, 10)}`} style={{ listStyle: "disc" }}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
