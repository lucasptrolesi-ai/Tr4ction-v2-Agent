"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NavLink = ({ href, children, icon }) => {
  const pathname = usePathname();
  const isActive = pathname === href || pathname?.startsWith(href + "/");
  
  return (
    <Link
      href={href}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
        padding: "10px 16px",
        borderRadius: "8px",
        fontSize: "14px",
        fontWeight: "500",
        color: isActive ? "#f8fafc" : "#94a3b8",
        background: isActive ? "rgba(0, 188, 212, 0.15)" : "transparent",
        border: isActive ? "1px solid rgba(0, 188, 212, 0.3)" : "1px solid transparent",
        transition: "all 0.2s ease",
        textDecoration: "none",
      }}
      onMouseEnter={(e) => {
        if (!isActive) {
          e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
          e.currentTarget.style.color = "#f8fafc";
        }
      }}
      onMouseLeave={(e) => {
        if (!isActive) {
          e.currentTarget.style.background = "transparent";
          e.currentTarget.style.color = "#94a3b8";
        }
      }}
    >
      <span style={{ fontSize: "18px" }}>{icon}</span>
      {children}
    </Link>
  );
};

export default function AdminLayout({ children }) {
  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)",
      fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
    }}>
      {/* Header */}
      <header style={{
        padding: "16px 32px",
        background: "rgba(15, 23, 42, 0.8)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}>
        <div style={{
          maxWidth: "1400px",
          margin: "0 auto",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, #00BCD4 0%, #00ACC1 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "20px",
              fontWeight: "700",
              color: "white",
            }}>
              A
            </div>
            <div>
              <h1 style={{
                margin: 0,
                fontSize: "18px",
                fontWeight: "700",
                background: "linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}>
                TR4CTION Admin
              </h1>
              <p style={{ margin: 0, fontSize: "12px", color: "#64748b" }}>
                Centro de Controle FCJ
              </p>
            </div>
          </div>

          {/* Navigation */}
          <nav style={{ display: "flex", gap: "8px" }}>
            <NavLink href="/admin" icon="📊">Dashboard</NavLink>
            <NavLink href="/admin/knowledge" icon="📚">Base de Conhecimento</NavLink>
            <NavLink href="/admin/trails" icon="🛤️">Trilhas</NavLink>
            <NavLink href="/admin/users" icon="👥">Usuários</NavLink>
          </nav>

          {/* User Badge */}
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "6px 12px",
            background: "rgba(34, 197, 94, 0.1)",
            border: "1px solid rgba(34, 197, 94, 0.2)",
            borderRadius: "999px",
            fontSize: "12px",
            color: "#22c55e",
          }}>
            <div style={{
              width: "8px",
              height: "8px",
              background: "#22c55e",
              borderRadius: "50%",
              boxShadow: "0 0 8px #22c55e",
            }}></div>
            Admin FCJ
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{
        maxWidth: "1400px",
        margin: "0 auto",
        padding: "32px",
      }}>
        {children}
      </main>
    </div>
  );
}
