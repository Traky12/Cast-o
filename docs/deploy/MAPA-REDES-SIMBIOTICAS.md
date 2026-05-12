# Mapa — redes simbióticas (visualización)

**Relación:** [PRONTUARIO-MAESTRO-ECOLOGIA-DIGITAL-AGRICOLA-2026.md](./PRONTUARIO-MAESTRO-ECOLOGIA-DIGITAL-AGRICOLA-2026.md) · [PRONTUARIO-MAESTRO-INTEGRACION-BIOLOGICA-DIGITAL-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-BIOLOGICA-DIGITAL-2026.md)

Los diagramas son **lenguaje de diseño** para alinear equipos agronómicos y de software. Las cajas “TraceChain”, “Grafana” o “memristor” deben interpretarse según lo **realmente desplegado** en cada entorno.

---

## 1. Ciclo datos ↔ decisión ↔ campo

```mermaid
flowchart TD
    A[Cultivo / objetivo agronómico] -->|Telemetría| B[Edge / gateway]
    B -->|Payload validado| C[API CASTÚO]
    C -->|Inferencia lab SNN| D[Caché / respuesta]
    D -->|Opcional| E[Trazabilidad TraceChain]
    E -->|Auditoría| F[Operador / agricultor]
    F -->|Decisión humana| A
    C --> G[Métricas Prometheus]
    G --> H[Grafana u observabilidad]
    H --> F
```

---

## 2. Red simbiótica pedagógica *(versión narrativa)*

```mermaid
flowchart LR
    subgraph rizosfera_digital [Intercambio]
        P[Parcela / planta]
        S[Sensores]
        M[Modelos e inferencia]
    end
    P <--> S
    S <--> M
    M -->|Recomendación trazable| O[Operación]
    O --> P
```

---

## 3. Flujo neuromórfico lógico *(alineado al stub en repo)*

Ver diagrama detallado en [NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md §1.1](../integrations/NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md).

---

*Si el diagrama no coincide con el cableado real del invernadero o del VPS, actualizar este mapa: el territorio gana a la metáfora.*
