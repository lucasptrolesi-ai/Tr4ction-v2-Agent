import Link from "next/link";

export default function FounderHome() {
  return (
    <div>
      <h1>Bem-vindo, founder</h1>
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
      </div>
    </div>
  );
}
