# Roadmap de robótica y señales (2026) — Castúo-System

**Estado:** laboratorio en repo; **no** certifica cumplimiento AI Act ni homologación de máquinas por sí solo.

**Código:** `backend/integrations/robotics/` · UI estática: `frontend/public/robotics-lab/` · Legal: [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md) · Neuromórfico (sim): [ROADMAP-Neuromorphic-2026.md](./ROADMAP-Neuromorphic-2026.md) · Scan3D→Print (sim): [ROADMAP-Scan3D-Print-2026.md](./ROADMAP-Scan3D-Print-2026.md)

---

## 1. Módulos y honestidad técnica

| Módulo | Estado en clon | Notas |
|--------|----------------|-------|
| Signal Manager (PCM lab + AES-GCM) | Esqueleto importable | GNU Radio / SDR: ver `GNU_RADIO.md`; IQ fuera del monolito por defecto. |
| Evolution Engine | GA integrado + DEAP opcional | `requirements-optional.txt` |
| Security / PQC | Reusa `pq_crypto.py` | Kyber real si `pqcrypto`; si no, ruta documentada en módulo. |
| Trazabilidad | `build_robot_evolution_audit_payload` | Mismo contrato que `register_event_in_chain` (`tokenId` int). |
| Lab stub → cadena | `lab_gaiachain_optional` | Opt-in `CASTUO_ROBOTICS_LAB_CHAIN_REGISTER=1` + `GAIA_*`; usa `register_event_in_chain` real (no servicio inventado). |
| HRI WebRTC | Stub estático | Requiere signaling propio + DPIA si hay datos personales en vídeo/audio. |

---

## 2. Integraciones externas (fuera de este roadmap como “hechas”)

- **ROS2:** nodo puente en máquina del robot, no en el wheelhouse del backend actual.
- **GaiaChain:** solo vía `gaiachain_service` con RPC/contrato configurados en despliegue.
- **QKD / “cuántico” de red:** no figura como dependencia del repositorio.

---

## 3. Hitos sugeridos

1. Definir `ROBOT_SIGNAL_SYMMETRIC_KEY` en Vault / rotación documentada.  
2. Piloto ROS2 → API interna con JWT y rate limits.  
3. DPIA revisada si se graban operadores o entornos identificables.  

---

*Documento orientativo; decisión jurídica final es humana.*
