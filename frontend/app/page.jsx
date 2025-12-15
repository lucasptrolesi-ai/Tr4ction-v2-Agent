import Link from "next/link";

export default function HomePage() {
  return (
    <div className="main-shell">
      <div className="landing-container">
        <div style={{ display: "flex", justifyContent: "space-between", gap: 24 }}>
          <div style={{ flex: 1.6 }}>
            <div className="chip">
              <span className="badge-live" />
              Versão 2.0 • FCJ Traction Program
            </div>

            <h1 style={{ marginTop: 18, marginBottom: 12 }}>
              TR4CTION Agent
            </h1>
            <p style={{ color: "var(--text-muted)", maxWidth: 520 }}>
              Painel unificado para founders e time FCJ: orientação guiada,
              templates oficiais, histórico de evolução e insights de marketing
              em um único lugar.
            </p>

            <div style={{ marginTop: 28, display: "flex", gap: 12 }}>
              <Link href="/login">
                <button className="btn btn-primary">
                  Fazer Login
                </button>
              </Link>
              <Link href="/register">
                <button className="btn btn-ghost">
                  Criar Conta
                </button>
              </Link>
            </div>

            <div style={{ marginTop: 18, fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Sistema autenticado com JWT. Founders e Admins possuem áreas distintas.
            </div>
          </div>

          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12 }}>
            <div className="card">
              <div className="card-title">Status geral</div>
              <div className="card-subtitle">Preview rápido dos squads</div>
              <ul style={{ paddingLeft: 18, fontSize: "0.8rem", marginTop: 8 }}>
                <li>Q1 Marketing Track • 12 startups</li>
                <li>ICP + Persona completos em 7/12</li>
                <li>SWOT em revisão para 3 casos</li>
              </ul>
            </div>

            <div className="card">
              <div className="card-title">Como usar?</div>
              <ol style={{ paddingLeft: 18, fontSize: "0.8rem", marginTop: 8 }}>
                <li>Founders acessam o módulo “Founder”</li>
                <li>Mentores e equipe FCJ usam o módulo “Admin”</li>
                <li>O agente lê os materiais oficiais do Q1 via RAG</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
