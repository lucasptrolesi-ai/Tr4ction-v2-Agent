"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import axios from "axios";

export default function StepSchemaPage() {
  const params = useParams();
  const router = useRouter();
  const { trailId, stepId } = params;
  const backendBase = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editedSchema, setEditedSchema] = useState("");

  useEffect(() => {
    loadSchema();
  }, [trailId, stepId]);

  async function loadSchema() {
    try {
      setLoading(true);
      const res = await axios.get(`${backendBase}/admin/trails/${trailId}/steps/${stepId}/schema`);
      setSchema(res.data);
      setEditedSchema(JSON.stringify(res.data, null, 2));
    } catch (err) {
      console.error("Erro ao carregar schema:", err);
      // Schema mock para desenvolvimento
      const mockSchema = {
        step_id: stepId,
        step_name: stepId.toUpperCase(),
        fields: [
          {
            name: "example_field",
            type: "text",
            label: "Campo de Exemplo",
            placeholder: "Digite aqui...",
            required: true
          }
        ]
      };
      setSchema(mockSchema);
      setEditedSchema(JSON.stringify(mockSchema, null, 2));
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    try {
      const parsedSchema = JSON.parse(editedSchema);
      const res = await axios.put(
        `${backendBase}/admin/trails/${trailId}/steps/${stepId}/schema`,
        parsedSchema
      );
      setSchema(res.data);
      setEditing(false);
      alert("Schema salvo com sucesso!");
    } catch (err) {
      console.error("Erro ao salvar:", err);
      alert("Erro ao salvar schema: " + (err.response?.data?.detail || err.message));
    }
  }

  if (loading) {
    return (
      <div>
        <h1>Carregando schema...</h1>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", alignItems: "center", gap: 12 }}>
        <button 
          onClick={() => router.back()} 
          className="btn btn-ghost"
          style={{ padding: "8px 16px" }}
        >
          ← Voltar
        </button>
        <h1 style={{ margin: 0 }}>
          Schema: {schema?.step_name || stepId}
        </h1>
      </div>

      <p style={{ color: "var(--text-muted)", maxWidth: 620, marginBottom: 32 }}>
        Revise e edite o schema desta etapa. O schema define os campos do formulário
        que os founders irão preencher.
      </p>

      <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        <button 
          className={editing ? "btn btn-ghost" : "btn btn-primary"}
          onClick={() => setEditing(!editing)}
        >
          {editing ? "❌ Cancelar" : "✏️ Editar Schema"}
        </button>
        
        {editing && (
          <button className="btn btn-primary" onClick={handleSave}>
            💾 Salvar Alterações
          </button>
        )}
      </div>

      {editing ? (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Editor JSON</h3>
          <textarea
            value={editedSchema}
            onChange={(e) => setEditedSchema(e.target.value)}
            style={{
              width: "100%",
              minHeight: 400,
              fontFamily: "monospace",
              fontSize: "0.9rem",
              padding: 12,
              border: "1px solid var(--border)",
              borderRadius: 8,
              background: "#f5f5f5"
            }}
          />
        </div>
      ) : (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Schema Atual</h3>
          
          {schema?.fields && schema.fields.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {schema.fields.map((field, idx) => (
                <div 
                  key={idx}
                  style={{
                    padding: 16,
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    background: "#fafafa"
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: 8 }}>
                    {field.label || field.name}
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: 4 }}>
                    <strong>Nome:</strong> {field.name}
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: 4 }}>
                    <strong>Tipo:</strong> {field.type}
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: 4 }}>
                    <strong>Obrigatório:</strong> {field.required ? "Sim" : "Não"}
                  </div>
                  {field.placeholder && (
                    <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                      <strong>Placeholder:</strong> {field.placeholder}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: "var(--text-muted)" }}>
              Nenhum campo definido no schema.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
