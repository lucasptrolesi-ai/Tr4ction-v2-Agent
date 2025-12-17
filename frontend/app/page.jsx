import { redirect } from "next/navigation";

export default function HomePage() {
  // Redireciona direto para o agente sem login
  redirect("/founder/chat");
}

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
