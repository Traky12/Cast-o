import React, { useState } from "react";
import { GridIoT } from "./GridIoT";

const trays = Array.from({ length: 48 }, (_, i) => {
  const id = (i + 1).toString().padStart(3, "0");
  return `B${id}`;
});

export function AgentDashboard() {
  const [selected, setSelected] = useState("B001");

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "radial-gradient(circle at top, #0f172a, #020617 60%)",
        color: "#e5e7eb",
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        padding: "2rem",
      }}
    >
      <h1 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "0.5rem" }}>
        Castúo Sabionda · TRL9
      </h1>
      <p style={{ opacity: 0.8, marginBottom: "1.5rem" }}>
        48 agentes autónomos monitorizando bandejas B001–B048, blockchain + tokenización.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 3fr", gap: "2rem" }}>
        <div>
          <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>Bandejas IoT</h2>
          <GridIoT selected={selected} onSelect={setSelected} />
        </div>

        <div
          style={{
            background: "rgba(15,23,42,0.9)",
            borderRadius: "1rem",
            padding: "1.25rem 1.5rem",
            border: "1px solid #1e293b",
          }}
        >
          <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>
            Agente {selected} · Estado
          </h2>
          <p style={{ fontSize: "0.9rem", opacity: 0.8, marginBottom: "0.75rem" }}>
            Aquí se puede conectar el chat del agente Mistral y el histórico on-chain
            (VeChain) + recompensas CASTUO Token para esta bandeja.
          </p>
          <ul style={{ fontSize: "0.85rem", lineHeight: 1.6 }}>
            <li>• Última decisión: pendiente de integrar stream de `/sabionda/decide`.</li>
            <li>• Blockchain: registro SIEX → VeChain vía `vechain_client`.</li>
            <li>• Tokenización: recompensas CASTUO Token vía `castuo_token`.</li>
            <li>• Notificaciones: bot Telegram/WhatsApp específico por bandeja.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

