# Hidroponía agrovoltaica — TRL7 (v1.3.2)

**CASTÚO 360 S.L.** | NFT, DWC, EbbFlow, Aeroponia bajo paneles solares

---

## Sistemas implementados

- **NFT:** 12 canales, 288 lechugas
- **DWC:** Albahaca, microgreens

## Sensores monitoreados

| Parámetro | Rango óptimo | Endpoint |
|-----------|--------------|----------|
| EC | 0.5–3.5 mS/cm | `/hidroponia/sensores` |
| pH | 5.5–6.5 | `/hidroponia/sensores` |
| DO | 6.0–8.0 mg/L | `/hidroponia/sensores` |
| Temp | 18–24 °C | `/hidroponia/sensores` |

## ROI hidroponía + solar

1 ha: Lechuga €34.5K + Energía 1 MWp €45K = **€79.5K/año** (+40% vs tradicional).

## API (backend 8001)

- `GET /hidroponia/sistemas` — listar sistemas
- `POST /hidroponia/sensores` — enviar EC, pH, DO, temp (JSON)
- `GET /hidroponia/cultivos` — listar cultivos
- `GET /hidroponia/alertas?ec=&ph=` — alertas

Deploy: `docker-compose --profile hidroponia up -d`

[Volver a Introducción](index.md)
