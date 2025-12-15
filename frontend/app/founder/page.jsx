import Link from "next/link";

export default function FounderHome() {
  return (
    <div>
      <h1>Bem-vindo, founder 👋</h1>
      <p style={{ color: "var(--text-muted)", maxWidth: 620 }}>
        Use o agente para preencher os templates oficiais (ICP, Persona, SWOT,
        Funil, Conteúdo, KPIs) e acompanhar seu progresso ao longo do programa.
      </p>

      <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
        <Link href="/founder/chat">
          <button className="btn btn-primary">Começar pelo chat</button>
        </Link>
        <Link href="/founder/templates">
          <button className="btn btn-ghost">Ver templates</button>
        </Link>
        <Link href="/founder/dashboard">
          <button className="btn btn-ghost">Dashboard</button>
        </Link>
      </div>

      <div style={{ marginTop: 32 }}>
        <div className="card">
          <h3>Próximos Passos</h3>
          <ul style={{ fontSize: "0.9rem", lineHeight: 1.8 }}>
            <li>Definir ICP (Ideal Customer Profile)</li>
            <li>Criar Personas detalhadas</li>
            <li>Análise SWOT da startup</li>
            <li>Mapear funil de marketing</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
