import Link from "next/link";

export default function FounderLayout({ children }) {
  return (
    <div className="main-shell">
      <div style={{ maxWidth: 960, width: "100%", margin: "32px 16px" }}>
        <header
          style={{
            marginBottom: 18,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center"
          }}
        >
          <div>
            <h2 style={{ margin: 0 }}>TR4CTION • Founder</h2>
            <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Seu copiloto para organizar marketing e tração.
            </p>
          </div>
          <nav style={{ display: "flex", gap: 10, fontSize: "0.85rem" }}>
            <Link href="/founder/chat">Chat</Link>
            <Link href="/founder/templates">Templates</Link>
            <Link href="/founder/dashboard">Dashboard</Link>
          </nav>
        </header>

        {children}
      </div>
    </div>
  );
}
