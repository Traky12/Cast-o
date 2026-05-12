# Protocolo de consenso Castúo (borrador v0)

Define cómo la federación valida eventos críticos sin base única de confianza.

## 1. Alcance de eventos críticos

- Apertura contenedor residuos / radiológico.
- Actualización firmware nodo edge.
- Emisión o rotación clave HSM federada.
- Registro pieza Circular FAB en gemelo dron (ver manual biocomposite).

## 2. Quórum (propuesta inicial)

| Red | Votos mínimos | Notas |
|-----|---------------|-------|
| Rural densa | **4/7** nodos acreditados | Incluye al menos 1 auditor y 1 operador territorio |
| Red degradada | **2/3** del subconjunto alcanzable | Ventana 300 s; si no hay acuerdo → **congelar** acción |

## 3. Prueba criptográfica

- Payload canónico JSON → **SHA-3-512**.
- Cada nodo firma con clave de nodo (no confundir con firma oráculo BioCoin).
- Cadena Merkle diaria opcional para auditoría WORM (alineado [REGULATORY-MICA-REACH](../biocoin/REGULATORY-MICA-REACH.md)).

## 4. Split-brain

1. Detección: partición de red > TTL heartbeat.
2. **Modo solo-lectura** en ambas mitades para acciones destructivas.
3. Reconciliación: ventana de fusión con timestamp vectorial + decisión DAO si conflicto persistente.

## 5. Implementación

- Núcleo lógico en backend FastAPI + cola de eventos; persistencia por nodo.
- Este documento es **normativo de diseño** hasta cierre de auditoría.

---

*Iterar con legal y operaciones antes de despliegue producción.*
