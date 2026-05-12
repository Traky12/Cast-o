import React from "react";

export function TokenWallet({ address = "0x...", balance = 0 }) {
  return (
    <div
      style={{
        background: "linear-gradient(135deg, #0f172a, #020617)",
        borderRadius: "1rem",
        padding: "1rem 1.25rem",
        border: "1px solid #1f2937",
        color: "#e5e7eb",
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      <h2 style={{ fontSize: "1rem", marginBottom: "0.6rem" }}>CASTUO Wallet</h2>
      <div style={{ fontSize: "0.8rem", opacity: 0.85, marginBottom: "0.4rem" }}>
        Dirección
      </div>
      <div
        style={{
          fontSize: "0.85rem",
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
          marginBottom: "0.8rem",
        }}
      >
        {address}
      </div>
      <div style={{ fontSize: "0.8rem", opacity: 0.85, marginBottom: "0.3rem" }}>
        Balance
      </div>
      <div style={{ fontSize: "1.2rem", fontWeight: 700 }}>
        {balance.toLocaleString("es-ES", { maximumFractionDigits: 4 })} CASTUO
      </div>
    </div>
  );
}

