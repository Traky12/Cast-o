import React from "react";

const trays = Array.from({ length: 48 }, (_, i) => {
  const id = (i + 1).toString().padStart(3, "0");
  return `B${id}`;
});

export function GridIoT({ selected, onSelect }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(80px, 1fr))",
        gap: "0.75rem",
        padding: "1rem",
        background: "#020617",
        color: "#e5e7eb",
        borderRadius: "1rem",
      }}
    >
      {trays.map((t) => {
        const isActive = selected === t;
        return (
          <button
            key={t}
            onClick={() => onSelect?.(t)}
            style={{
              padding: "0.6rem 0.4rem",
              borderRadius: "0.75rem",
              border: isActive ? "2px solid #22c55e" : "1px solid #1f2937",
              background: isActive ? "rgba(34,197,94,0.12)" : "#020617",
              color: "#e5e7eb",
              fontSize: "0.8rem",
              fontWeight: 600,
              letterSpacing: "0.04em",
              cursor: "pointer",
              boxShadow: isActive
                ? "0 0 0 1px rgba(34,197,94,0.6), 0 10px 30px rgba(0,0,0,0.55)"
                : "0 8px 20px rgba(0,0,0,0.75)",
              transition:
                "transform 120ms ease, box-shadow 120ms ease, background 120ms ease, border-color 120ms ease",
            }}
          >
            {t}
          </button>
        );
      })}
    </div>
  );
}
